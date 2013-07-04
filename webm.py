from ctypes import cdll as loader
from ctypes import c_char_p, c_void_p, byref

webm = loader.LoadLibrary("/home/ian/workspace/IND/webm/libvpx/libvpx.so.1.2.0")

webm.vpx_codec_vp8_cx.restype = c_void_p
interface = webm.vpx_codec_vp8_cx()

webm.vpx_codec_iface_name.argtypes = [c_void_p]
webm.vpx_codec_iface_name.restype = c_char_p
print("Using ", webm.vpx_codec_iface_name(interface))


# interface = webm.vpx_codec_vp8_cx()
# 
# cfg = webm.vpx_codec_enc_cfg_t
# 
# res = webm.vpx_codec_enc_config_default(interface, byref(cfg), 0);
# if res:
#     printf("Failed to get config: %s\n", webm/vpx_codec_err_to_string(res));