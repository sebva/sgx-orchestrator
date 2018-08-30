#!/usr/bin/env python3
import sys

import os
import time
from concurrent import futures

import grpc

from api import api_pb2
from api import api_pb2_grpc

healthy = "Healthy"
unhealthy = "Unhealthy"
api_version = "v1beta1"
sgx_endpoint = 'sgx.sock'
resource_name = 'intel.com/sgx'
sgx_device_path = '/dev/isgx'
sgx_socket_path = '/var/lib/kubelet/device-plugins/' + sgx_endpoint
kubelet_socket_path = 'unix:///var/lib/kubelet/device-plugins/kubelet.sock'


class SgxPluginService(api_pb2_grpc.DevicePluginServicer):
    def ListAndWatch(self, request: api_pb2.Empty, context):
        print("Kubelet called ListAndWatch()")
        while True:
            total_epc = fetch_total_epc()
            print("Returning %d pages to ListAndWatch()" % total_epc)

            devices = [api_pb2.Device(ID=("sgx%d" % x), health=healthy) for x in range(total_epc)]
            yield api_pb2.ListAndWatchResponse(devices=devices)
            time.sleep(60)

    def Allocate(self, alloc_request: api_pb2.AllocateRequest, context):
        responses = []

        for request in alloc_request.container_requests:
            print("Allocate(%d pages)" % len(request.devicesIDs))

            responses += [
                api_pb2.ContainerAllocateResponse(
                    annotations=(),
                    envs=dict(),
                    mounts=[],
                    devices=[
                        api_pb2.DeviceSpec(
                            container_path=sgx_device_path,
                            host_path=sgx_device_path,
                            permissions='rw'
                        )] if index == 0 else []
                )
                for index, item in enumerate(request.devicesIDs)
            ]

        return api_pb2.AllocateResponse(container_responses=responses)

    def GetDevicePluginOptions(self, request, context):
        return api_pb2.DevicePluginOptions(pre_start_required=False)


def fetch_total_epc():
    try:
        with open('/sys/module/isgx/parameters/sgx_nr_total_epc_pages') as f:
            return int(f.readline())
    except FileNotFoundError:
        print("You are using the vanilla version of the Intel SGX driver. Using 93.5 MiB as EPC size.", file=sys.stderr)
        return 23936


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    api_pb2_grpc.add_DevicePluginServicer_to_server(SgxPluginService(), server)
    server.add_insecure_port('unix://' + sgx_socket_path)
    server.start()
    return server


def register():
    channel = grpc.insecure_channel(kubelet_socket_path)
    stub = api_pb2_grpc.RegistrationStub(channel)
    register_message = api_pb2.RegisterRequest(
        version=api_version,
        endpoint=sgx_endpoint,
        resource_name=resource_name,
        options=api_pb2.DevicePluginOptions(pre_start_required=False)
    )
    response = stub.Register(register_message)
    print("Client received: " + str(response))
    return response


def check_sgx():
    return os.path.exists('/dev/isgx')


if __name__ == '__main__':
    if not check_sgx():
        print("No SGX device detected, exiting...")
        exit(0)

    try:
        print("Starting deviceplugin server")
        server = serve()
        print("deviceplugin server started")
        print("Registering with Kubelet")
        if isinstance(register(), api_pb2.Empty):
            print("Registered, Kubelet should now call us back")
            try:
                while True:
                    time.sleep(3600)
            except KeyboardInterrupt:
                server.stop(0)
        else:
            print("Error with the registration, exiting...")
    except Exception as e:
        print(e)
        print("Error with the registration, exiting...")
