#!/usr/bin/env python3
import os
import time
from concurrent import futures

import grpc

from api import api_pb2
from api import api_pb2_grpc

healthy = "Healthy"
unhealthy = "Unhealthy"
sgx_socket_path = '/var/lib/kubelet/device-plugins/sgx.sock'
kubelet_socket_path = 'unix:///var/lib/kubelet/device-plugins/kubelet.sock'


class SgxPluginService(api_pb2_grpc.DevicePluginServicer):
    def ListAndWatch(self, request: api_pb2.Empty, context):
        print("Kubelet called ListAndWatch()")
        while True:
            total_epc = fetch_total_epc()
            print("Returning %d pages to ListAndWatch()" % total_epc)

            devices = [api_pb2.Device(ID=("sgx%d" % x), health=healthy) for x in range(total_epc)]
            yield api_pb2.ListAndWatchResponse(devices=devices)
            time.sleep(10)

    def Allocate(self, request: api_pb2.AllocateRequest, context):
        print("Allocate(%d pages)" % request)

        requested_ids = request.devicesIDs

        devices = []
        if len(requested_ids) > 0:
            device0 = [api_pb2.DeviceRuntimeSpec(
                ID=requested_ids[0],
                envs=dict(),
                mounts=[],
                devices=[
                    api_pb2.DeviceSpec(
                        container_path='/dev/isgx',
                        host_path='/dev/isgx',
                        permissions='rw'
                    )
                ]
            )]

            devices = device0 + [
                api_pb2.DeviceRuntimeSpec(
                    ID=x,
                    envs=dict(),
                    mounts=[],
                    devices=[]
                )
                for x in requested_ids[1:]
            ]

        return api_pb2.AllocateResponse(spec=devices)


def fetch_total_epc():
    with open('/sys/module/isgx/parameters/sgx_nr_total_epc_pages') as f:
        return int(f.readline())


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    api_pb2_grpc.add_DevicePluginServicer_to_server(SgxPluginService(), server)
    server.add_insecure_port('unix://' + sgx_socket_path)
    server.start()
    return server


def register():
    channel = grpc.insecure_channel(kubelet_socket_path)
    stub = api_pb2_grpc.RegistrationStub(channel)
    register_message = api_pb2.RegisterRequest(version='0.1', endpoint='sgx.sock', resource_name='intel.com/sgx')
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
