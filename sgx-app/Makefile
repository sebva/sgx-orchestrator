CC             := gcc
CXX            := g++-5
SHELL          := /bin/bash
SGX            := 0

SrcDir         := src
SGX_COMMONDIR  := $(realpath ../../sgx-systems/sgx_common)

SgxToken       := sgx
NativeToken    := ntv

CFlags         := -m64
CPPFlags       := -std=c++11
TARGET         := dummy
Untrusted_Objs := $(TARGET).o
ENCLAVENAME    := enclave_$(TARGET)

ifeq ($(SGX),1)
BuildToken  := $(SgxToken)
else
BuildToken  := $(NativeToken)
endif

BinDir  := bin-$(BuildToken)
ObjDir  := obj-$(BuildToken)

SGX_SDK              := $(realpath ../../sgx-sdk)
SGX_LIBRARY_PATH     := $(SGX_SDK)/build/linux
SGX_ENCLAVE_SIGNER   := $(SGX_SDK)/build/linux/sgx_sign
SGX_EDGER8R          := $(SGX_SDK)/build/linux/sgx_edger8r

#SGX_SDK              := /opt/intel/sgxsdk
#SGX_LIBRARY_PATH     := $(SGX_SDK)/lib64
#SGX_ENCLAVE_SIGNER   := $(SGX_SDK)/bin/x64/sgx_sign
#SGX_EDGER8R          := $(SGX_SDK)/bin/x64/sgx_edger8r

IncludeSdk           := common/inc
IncludeDirs          += $(SGX_SDK)/$(IncludeSdk)
App_Libs             := sgx_capable
App_Lib_Dirs         := $(SGX_LIBRARY_PATH) 

ifeq ($(SGX),1)
TRUSTEDOBJS          := $(ENCLAVENAME)_t.o enclave_dummy.o 
Trts_Library_Name    := sgx_trts
Service_Library_Name := sgx_tservice
App_Libs             += sgx_uae_service sgx_urts 
CFlags               += -DENABLE_SGX
#IncludeDirs          += $(SGX_SDK)/include
Untrusted_Objs       += 
Untrusted_Objs       := $(filter-out $(TRUSTEDOBJS), $(Untrusted_Objs)) \
	                    $(ENCLAVENAME)_u.o
SGXCOMOBJS := $(addprefix $(ObjDir)/, sgx_initenclave.o sgx_errlist.o)
Enclave_Lib_Dirs     := $(SGX_LIBRARY_PATH) $(dir $(ExtLibs)) $(SGX_SDK)/sdk/libcapable/linux/
Enclave_Libs         := 
Enclave_SDK_Libs     := -Wl,--whole-archive \
                            -l$(Trts_Library_Name) \
                        -Wl,--no-whole-archive \
                        -Wl,--start-group \
                             $(addprefix -l, sgx_tstdc sgx_tstdcxx sgx_tcrypto \
                                             $(Service_Library_Name) ) \
                        -Wl,--end-group
Enclave_Link_Flags   := $(addprefix -L, $(Enclave_Lib_Dirs)) \
                        $(addprefix -l, $(Enclave_Libs)) \
                        $(Enclave_SDK_Libs)
Trusted_Link_Flags := -Wl,--no-undefined -nostdlib \
	-nodefaultlibs -nostartfiles $(Enclave_Link_Flags)  \
	-Wl,-Bstatic -Wl,-Bsymbolic -Wl,--no-undefined \
	-Wl,-pie,-eenclave_entry -Wl,--export-dynamic  \
	-Wl,--defsym,__ImageBase=0 \
	-Wl,--version-script=$(SrcDir)/$(ENCLAVENAME).lds
Common_C_Cpp_Flags := $(CFlags) -nostdinc -fvisibility=hidden \
	                  -fpie -fstack-protector -fno-builtin-printf
Enclave_C_Flags   := -Wno-implicit-function-declaration -std=c11 \
	                 $(Common_C_Cpp_Flags)
Enclave_Cpp_Flags := $(Common_C_Cpp_Flags) $(CPPFlags) -nostdinc++
Enclave_IncDirs   := $(SGX_SDK)/include/stlport $(SrcDir) \
                     $(SGX_SDK)/$(IncludeSdk) \
                     $(SGX_SDK)/$(IncludeSdk)/tlibc $(SGX_COMMONDIR) 
Enclave_Include   := $(addprefix -I, $(Enclave_IncDirs))
App_Cpp_Objs      := $(SGXCOMOBJS)
Trusted_Objects   := $(addprefix $(ObjDir)/,$(TRUSTEDOBJS))
all: $(BinDir)/$(TARGET) $(BinDir)/$(TARGET).signed.so
$(addprefix $(ObjDir)/,server_protocol.o $(TARGET).o): $(SrcDir)/$(ENCLAVENAME)_u.c
$(ObjDir)/query_manager.o : $(SrcDir)/$(ENCLAVENAME)_t.c
else
LDFLAGS      := -static
all: $(BinDir)/$(TARGET)
endif

IncludeDirs    += $(SrcDir) $(SGX_COMMONDIR)  
App_Include    := $(addprefix -I, $(IncludeDirs))
App_Link_Flags := $(addprefix -L, $(App_Lib_Dirs)) \
                  $(addprefix -l, $(App_Libs))
App_Cpp_Objs   += $(addprefix $(ObjDir)/, $(Untrusted_Objs))

############## UNTRUSTED #######################################################
$(BinDir)/$(TARGET): ${App_Cpp_Objs} | $(BinDir)
	${CXX} $^ -o $@ ${App_Link_Flags} ${LDFLAGS}
	@echo -e "LINK (App)\t=>\t$@"

$(ObjDir)/%.o : $(SrcDir)/%.c | $(ObjDir)
	@${CC} ${CFlags} ${App_Include} -c $< -o $@
	@echo -e "CC (App)\t<=\t$<"

$(ObjDir)/%.o : $(SrcDir)/%.cpp | $(ObjDir)
	@${CXX} ${CPPFlags} ${CFlags} ${App_Include} -c $< -o $@
	@echo -e "CXX (App)\t<=\t$<"

$(SGXCOMOBJS) : $(ObjDir)/%.o : $(SGX_COMMONDIR)/%.cpp | $(ObjDir)
	@${CXX} ${CPPFlags} ${CFlags} ${App_Include} -c $< -o $@
	@echo -e "CXX (App)\t<=\t$<"

$(SrcDir)/$(ENCLAVENAME)_u.c : $(SrcDir)/$(ENCLAVENAME).edl $(SGX_EDGER8R)
	@cd $(dir $@) && $(SGX_EDGER8R) --untrusted ../$< --search-path ../$(dir $<) --search-path $(SGX_SDK)/$(IncludeSdk)
	@echo -e "EDGER (App)\t=>\t$@"

############## TRUSTED #########################################################
$(BinDir)/$(TARGET).signed.so : %.signed.so : %.so
	@$(SGX_ENCLAVE_SIGNER) sign -enclave $< -config $(SrcDir)/$(ENCLAVENAME).config.xml -out $@ -key $(SrcDir)/enclave-key.pem
	@echo -e "SIGN (Enclave)\t=>\t$@"

$(BinDir)/$(TARGET).so : $(Trusted_Objects)
	$(CXX) $^ -o $@ $(Trusted_Link_Flags)
	@echo -e "LINK (Enclave)\t=>\t$@"

$(SrcDir)/$(ENCLAVENAME)_t.c : $(SrcDir)/$(ENCLAVENAME).edl $(SGX_EDGER8R)
	@cd $(dir $@) && $(SGX_EDGER8R) --trusted ../$< --search-path ../$(dir $<) --search-path $(SGX_SDK)/$(IncludeSdk)
	@echo -e "EDGER (Enclave)\t=>\t$@"

$(ObjDir)/$(ENCLAVENAME)_t.o : $(SrcDir)/$(ENCLAVENAME)_t.c
	@${CC} -c $< -o $@ ${Enclave_C_Flags} ${Enclave_Include} 
	@echo -e "CC (Enclave)\t<=\t$<"

$(ObjDir)/%_t.o : $(SGX_COMMONDIR)/libc_mock/%.c
	@${CC} -c $< -o $@ ${Enclave_C_Flags} ${Enclave_Include} 
	@echo -e "CC (Enclave)\t<=\t$<"

$(ObjDir)/%_t.o : $(SGX_COMMONDIR)/libc_mock/%.cpp
	@${CXX} -c $< -o $@ ${Enclave_Include} ${Enclave_Cpp_Flags}
	@echo -e "CXX (Enclave)\t<=\t$<"

$(filter-out %_t.o, $(Trusted_Objects)) : $(ObjDir)/%.o : $(SrcDir)/%.cpp
	@${CXX} -c $< -o $@ ${Enclave_Include} ${Enclave_Cpp_Flags}
	@echo -e "CXX (Enclave)\t<=\t$<"
################################################################################

$(BinDir):
	@mkdir $(BinDir)

$(ObjDir):
	@mkdir $(ObjDir)

.PHONY: clean 

clean:
	rm -rf $(BinDir) $(ObjDir) $(SrcDir)/*_{t,u}.{c,h} 

