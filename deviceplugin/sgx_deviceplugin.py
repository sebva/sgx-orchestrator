import time
from concurrent import futures

import grpc

from api import api_pb2
from api import api_pb2_grpc

sgx_socket_path = '/var/lib/kubelet/device-plugins/sgx.sock'
kubelet_socket_path = 'unix:///var/lib/kubelet/device-plugins/kubelet.sock'


class SgxPluginService(api_pb2_grpc.DevicePluginServicer):
    def ListAndWatch(self, request, context):
        pass

    def Allocate(self, request, context):
        pass


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    api_pb2_grpc.add_DevicePluginServicer_to_server(SgxPluginService(), server)
    server.add_insecure_port('unix://' + sgx_socket_path)
    server.start()
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        server.stop(0)


def register():
    channel = grpc.insecure_channel(kubelet_socket_path)
    stub = api_pb2_grpc.RegistrationStub(channel)
    register_message = api_pb2.RegisterRequest(version='0.1', endpoint=sgx_socket_path, resource_name='intel.com/sgx')
    response = stub.Register(register_message)
    print("Client received: " + response)
    return response


if __name__ == '__main__':
    register()
