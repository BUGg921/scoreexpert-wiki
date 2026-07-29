"""集合通信算法时间计算模块

数学原理：
    通信总时间 = 静态时延 + 数据传输时间
    静态时延 = base_static_delay * 通信次数 * delay_ratio
    数据传输时间 = 通信数据量 / 带宽

关键公式：
    - Ring AllReduce: 需2(N-1)步
      每步传输S/N的数据, 总传输数据量 = 2(N-1) / N * S
    - HD AllReduce: 利用递归二分, 需要 2log2(N)步
      总传输量与Ring相同
    - NHR: 对非2的幂次方的N, 利用sqrt(N)构造近方阵,
      行列分别做HD/Ring, 总步数约4 * sqrt(N)
"""
import math

BASIC_STATIC_DELAY = 60e-6

Gb = 1024**3
GB = 1024**3 * 8

# ============================ AllReduce算法 ============================
def ring_time(dp_devices, rhd_data, band, base_delay=BASIC_STATIC_DELAY, delay_ratio=1):
    """Ring AllReduce算法时间计算
    
    Args:
        dp_devices: 参与通信的设备数量
        rhd_data: 通信数据量
        band: 带宽
        base_delay: 基础静态时延
        delay_ratio: 时延比例
    """
    transfer_time = 2 * (dp_devices - 1) * (rhd_data / dp_devices / band)
    static_delay = base_delay * delay_ratio * 2 * (dp_devices - 1)
    return transfer_time + static_delay

def get_2ring_time(dp_devices, rhd_data, band, base_delay=BASIC_STATIC_DELAY, delay_ratio=1):
    """获取2Ring AllReduce算法时间
    
    算法: 两个910C卡做相反方向的ring, 单ring传输量减半
    传输时间: (N-1) / N * S / band

    Args:
        dp_devices: 参与通信的设备数量
        rhd_data: 通信数据量
        band: 带宽
        base_delay: 基础静态时延
        delay_ratio: 时延比例
    """
    static_delay = base_delay * delay_ratio * 2 * (dp_devices - 1)
    total_data = (dp_devices - 1) * rhd_data / dp_devices
    return static_delay + total_data / band

def get_nhr_time(dp_devices, data_size, band, base_delay=BASIC_STATIC_DELAY, delay_ratio=1):
    """NHR V1 (Non-power-of-two Hierarchical Ring)时间计算

    算法: 对N个设备, 构造 vxv 或者 vx(v+1)近方阵,
    行列分别做HD/Ring, 总步数约4 * sqrt(N)
    v = floor(sqrt(N))
    
    通信次数:
      N = v^2    -> 4(v-1)步
      v^2 < N < v(v+1) -> 4(v-2)步
      N = v(v+1)    -> 4(v-2)步
      v(v+1) < N < (v+1)^2 -> 4v步
    Args:
        dp_devices: 参与通信的设备数量
        data_size: 通信数据量
        band: 带宽
    """
    v = math.floor(math.sqrt(dp_devices))
    if dp_devices < v * (v+1):
      if dp_devices == v * v:
        static_delay = base_delay * delay_ratio * 4 * (v-1)
        #N = v^2: 行环传输(v-1)/v*S, 列环传输(v-1)/v/v*S
        transfer_time = 2 * ((v-1) / v + (v-1) / v / v) * data_size / band
      else:
        static_delay = base_delay * delay_ratio * 4 * (v-2)
        #v^2 < N < v(v+1): 行环传输*S, 列环传输(v-2)/v/v*S
        transfer_time = 2 * (1 + (v-1) / v / v) * data_size / band
    else:
      if dp_devices == v * (v+1):
        static_delay = base_delay * delay_ratio * 4 * (v-2)
        #N = v(v+1): 行环传输(v-1)/v*S, 列环传输1/(v+1)*S
        transfer_time = 2 * ((v-1) / v + 1 / (v+1)) * data_size / band
      else:
        static_delay = base_delay * delay_ratio * 4 * v
        #v(v+1) < N < (v+1)^2: S, 列环传输1/(v+1)*S
        transfer_time = 2 * (1 + 1 / (v+1)) * data_size / band
    return static_delay + transfer_time

def get_nhr_2band_theory(dp_devices, data_size, hccs_band, roce_band, intra_node_size, base_delay=BASIC_STATIC_DELAY, delay_ratio=1):
  """NHR V2 双带宽理论模型(区分亲合组内/间带宽)
  
  算法: 行环走HCCS带宽, 列环走ROCE带宽
  v = floor(sqrt(N)), 行维度=亲合组大小, 列维度=亲合组数

  Args:
    dp_devices: 参与通信的设备数量
    data_size: 通信数据量
    hccs_band: HCCS带宽
    roce_band: ROCE带宽
    intra_node_size: 一个亲合组内设备数量
  """
  v = math.floor(math.sqrt(dp_devices))
  if dp_devices < v * (v+1):
    hops = 4 * v-2 if dp_devices != v * v else 4 * v-1
  else:
    hops = 4 * v
  static_delay = base_delay * delay_ratio * hops

  #传输时间：alpha为行环占比, beta为列环占比
  if dp_devices == v * v:
    alpha = (v-1) / v
    beta = (v-1) / v / v
  elif dp_devices < v * (v+1):
    alpha = 1.0
    beta = (v-1) / v / v
  elif dp_devices == v * (v+1):
    alpha = (v-1) / v
    beta = 1.0 / (v+1)
  else:
    alpha = 1.0
    beta = 1.0 / (v+1)
  
  transfer_time = (alpha * data_size / hccs_band + beta * data_size / roce_band) * 2
  return static_delay + transfer_time

def get_nhr_2band(dp_devices, data_size, hccs_band, roce_band, intra_node_size, base_delay=BASIC_STATIC_DELAY, delay_ratio=1):
  """NHR V2 双带宽实际模型(区分亲合组内/间带宽)

  与理论版本的区别主要在于: 行维度固定为亲合组大小(intra_node_size), 列维度=N/intra_node_size
  三阶段: 行RS -> 列AR -> 行AG

  Args:
    dp_devices: 参与通信的设备数量
    data_size: 通信数据量
    hccs_band: HCCS带宽
    roce_band: ROCE带宽
    intra_node_size: 一个亲合组内设备数量
  """

  v = intra_node_size
  m = dp_devices // v

  hops = (v-1) + 2 * (m-1) + (v-1)
  static_delay = base_delay * delay_ratio * hops

  alpha = (v-1) / v
  beta = (m-1) / m / v

  transfer_time = (alpha * data_size / hccs_band + beta * data_size / roce_band) * 2
  return static_delay + transfer_time

def get_rhd_time(dp_devices, rhd_data, band, base_delay=BASIC_STATIC_DELAY, delay_ratio=1):
  """RHD (Reduced Halving-Doubling)时间计算
  算法: 当N不是2的幂次方时使用, 在2^floor(log2(N))个设备上做HD
  剩余设备用额外三次同步

  args:
    dp_devices: 参与通信的设备数量
    rhd_data: 通信数据量
    band: 带宽
  """
  comm_times = math.floor(math.log2(dp_devices))
  if dp_devices < 2 ** math.ceil(math.log2(dp_devices)):
    total_data = 2 * (2-1/2**comm_times) * rhd_data
    static_delay = base_delay * delay_ratio * (2 * comm_times + 3)
  else:
    total_data = 2 * (1 - 1/dp_devices) * rhd_data
    static_delay = base_delay * delay_ratio * (2 * comm_times)
  return total_data / band + static_delay


def get_nb_time(dp_devices, nb_size, band, base_delay=BASIC_STATIC_DELAY, delay_ratio=1):
  comm_times = math.ceil(math.log2(dp_devices))
  static_delay = base_delay * delay_ratio * (2 * comm_times)
  transfer_time = 2 * (dp_devices - 1) /dp_devices * nb_size / band
  return static_delay + transfer_time


