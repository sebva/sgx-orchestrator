#!/usr/bin/env python3
import time
from concurrent import futures

import grpc
import os

from api import api_pb2
from api import api_pb2_grpc

healthy = "Healthy"
unhealthy = "Unhealthy"
sgx_socket_path = '/var/lib/kubelet/device-plugins/sgx.sock'
kubelet_socket_path = 'unix:///var/lib/kubelet/device-plugins/kubelet.sock'


class SgxPluginService(api_pb2_grpc.DevicePluginServicer):
    def ListAndWatch(self, request, context):
        print("ListAndWatch(%s, %s)" % (request, context))
        while True:
            yield api_pb2.ListAndWatchResponse(devices=[
                api_pb2.Device(
                    ID="sgx1",
                    health=healthy
                )
            ])
            time.sleep(5)

    def Allocate(self, request, context):
        print("Allocate(%s, %s)" % (request, context))
        return api_pb2.AllocateResponse(spec=[
            api_pb2.DeviceRuntimeSpec(
                ID='sgx1',
                envs=dict(),
                mounts=[],
                devices=[
                    api_pb2.DeviceSpec(
                        container_path='/dev/sgx',
                        host_path='/dev/sgx',
                        permissions='rw'
                    )
                ]
            )
        ])


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
