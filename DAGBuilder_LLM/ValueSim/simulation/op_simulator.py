import math
from enum import Enum

class Layer3Algorithm(Enum):
    """L2层(RDMA)算法枚举"""
    NHR = "NHR"
    RING = "RING"

class Layer2Algorithm(Enum):
    """L1层(HCCS)算法枚举"""
    NHR = "NHR"
    RING = "RING"

class Layer1Algorithm(Enum):
    """L0层(Ring HCCS)算法枚举"""
    RING = "RING"
    MESH = "MESH"

class AllGatherModel:
    def __init__(self, total_data_size, domain_size, node_size, affinity_group_size, roce_bandwidth, hccl_bandwidtg, base_static_delay_layer1=60e-6, base_static_delay_layer2=60e-6, base_static_delay_layer3=60e-6):
        self.S = total_data_size            #总通信量
        self.K = domain_size                #通信域大小
        self.N1 = node_size                 #节点内
        self.N2 = affinity_group_size       #亲合组内
        self.N3 = domain_size // (node_size * affinity_group_size) #亲合组外
        self.N1 = int(self.N1)
        self.N2 = int(self.N2)
        self.N3 = int(self.N3)

        self.roce_bw = roce_bandwidth       #RoCE带宽
        self.hccl_bw = hccl_bandwidtg       #HCCS带宽

        self.base_static_delay_layer1 = base_static_delay_layer1 #L1层静态延迟
        self.base_static_delay_layer2 = base_static_delay_layer2 #L2层静态延迟
        self.base_static_delay_layer3 = base_static_delay_layer3 #L3层静态延迟

        #默认算法配置
        self.layer3_algorithm = Layer3Algorithm.NHR
        self.layer2_algorithm = Layer2Algorithm.NHR
        self.layer1_algorithm = Layer1Algorithm.RING

        if self.N3 * self.N2 * self.N1 != self.K:
            raise ValueError(f"{self.N3} * {self.N2} * {self.N1} != {self.K}")

    def set_algorithms(self, layer3_alg=None, layer2_alg=None, layer1_alg=None):
        if layer3_alg:
            self.layer3_algorithm = layer3_alg
        if layer2_alg:
            self.layer2_algorithm = layer2_alg
        if layer1_alg:
            self.layer1_algorithm = layer1_alg

    def calculate_steps(self):
        M3 = math.ceil(math.log2(self.N3)) if self.N3 > 1 else 0 #亲合组外步数
        M2 = int(math.log2(self.N2)) if self.N2 > 1 else 0 #亲合组内步数
        M1 = self.N1 - 1 if self.N1 > 1 else 0 #节点内步数
        return M3, M2, M1

    def calculate_static_delay(self, comm_times):
        return self.base_static_delay_layer

    def calculate_layer3_time(self, algorithm=None):
        """计算亲合组外时间"""
        if self.N3 <=1:
            return 0, 0, []
        
        current_algorithm = algorithm if algorithm else self.layer3_algorithm

        if current_algorithm == Layer3Algorithm.NHR:
            M3 = math.ceil(math.log2(self.N3)) if self.N3 > 1 else 0;
        elif current_algorithm == Layer3Algorithm.RING:
            M3 = self.N3 - 1 if self.N3 > 1 else 0;
        else:
            M3 = math.ceil(math.log2(self.N3)) if self.N3 > 1 else 0;

        total_time = 0
        total_static_delay = 0
        time_details = []

        for step in range(M3):
            #根据算法确定通信次数和通信量
            if current_algorithm == Layer3Algorithm.NHR:
                #NHR算法，每步通信量翻倍，通信次数为1
                data_size = self.S / self.K * (2 ** step)
                comm_times = 1
                static_delay = self.base_static_delay_layer3 * (2 ** step)
            elif current_algorithm == Layer3Algorithm.RING:
                #RING算法，每步通信量不变，通信次数为2
                data_size = self.S / self.K
                comm_times = 2
                static_delay = self.base_static_delay_layer3
            else:
                #默认使用NHR算法
                data_size = self.S / self.K * (2 ** step)
                comm_times = 1
                static_delay = self.base_static_delay_layer3 * (2 ** step)

            #计算每步通信时间
            transfer_time = data_size / self.roce_bw
            total_step_time = transfer_time + static_delay
            total_time += total_step_time
            total_static_delay += static_delay

            time_details.append({
                'layer': 'L2(RDMA)',
                'algorithm': current_algorithm.value,
                'step': step,
                'data_size': data_size,
                'transfer_time': transfer_time,
                'static_delay': static_delay,
                'total_time': total_step_time,
                'comm_times': comm_times
            })

            return total_time, total_static_delay, time_details

    def calculate_layer2_time(self, algorithm=None):
        """计算亲合组内通信时间"""
        if self.N2 <=1:
            return 0, 0, []

        current_algorithm = algorithm if algorithm else self.layer2_algorithm

        if current_algorithm == Layer2Algorithm.NHR:
            M2 = math.log2(self.N2) if self.N2 > 1 else 0;
        elif current_algorithm == Layer2Algorithm.RING:
            M2 = self.N2 - 1 if self.N2 > 1 else 0;
        else:
            M2 = math.log2(self.N2) if self.N2 > 1 else 0;
        M3=self.N2-1 if self.N2 > 1 else 0;
        total_time = 0
        total_static_delay = 0
        time_details = []

        for step in range(M2):
            if current_algorithm == Layer2Algorithm.NHR:
                #每步通信量=S/K *2^(M3+step)
                #NHR算法，每步通信量翻倍，通信次数为1
                data_size = self.S / (self.N2 * self.N1) * 2**(step)
                comm_times = 1
                static_delay = self.base_static_delay_layer2 * 2 ** (M3 + step)
            if current_algorithm == Layer2Algorithm.RING:
                #RING算法，每步通信量不变，通信次数为1
                data_size = self.S / (self.N2 * self.N1)
                comm_times = 1
                static_delay = self.base_static_delay_layer2 * 2 ** M3
            
            #计算每步通信时间
            transfer_time = data_size / self.hccl_bw
            total_step_time = transfer_time + static_delay
            total_time += total_step_time
            total_static_delay += static_delay

            time_details.append({
                'layer': 'L1(HCCS)',
                'step': step,
                'data_size': data_size,
                'transfer_time': transfer_time,
                'static_delay': static_delay,
                'total_time': total_step_time,
                'comm_times': comm_times
            })

        return total_time, total_static_delay, time_details

    def calculate_layer1_time(self, algorithm=None):
        """计算片上网络通信时间"""
        if self.N1 <=1:
            return 0, 0, []

        current_algorithm = algorithm if algorithm else self.layer1_algorithm
        if current_algorithm == Layer1Algorithm.RING:
            M1 = self.N1 - 1 if self.N1 > 1 else 0;
        elif current_algorithm == Layer1Algorithm.MESH:
            #MESH算法，只传输一次
            M1 = 1;
        else:
            M1 = self.N1 - 1 if self.N1 > 1 else 0;
        
        M3 = math.ceil(math.log2(self.N3)) if self.N3 > 1 else 0;
        M2 = math.ceil(math.log2(self.N2)) if self.N2 > 1 else 0;
        total_time = 0
        total_static_delay = 0
        time_details = []

        data_size = self.S / self.N1
        for step in range(M1):
            transfer_time = data_size / self.hccl_bw
            comm_times = 1
            static_delay = self.base_static_delay_layer1 * (2 ** (M3 + M2))

            total_step_time = transfer_time + static_delay
            total_time += total_step_time
            total_static_delay += static_delay

            time_details.append({
                'layer': 'L0(Ring HCCS)',
                'step': step,
                'data_size': data_size,
                'transfer_time': transfer_time,
                'static_delay': static_delay,
                'total_time': total_step_time,
                'comm_times': comm_times
            })

        return total_time, total_static_delay, time_details

    def calculate_total_time(self):
        M1,M2,M3 = self.calculate_steps()

        time_l3, static_delay_l3, details_l3 = self.calculate_layer3_time()
        time_l2, static_delay_l2, details_l2 = self.calculate_layer2_time()
        time_l1, static_delay_l1, details_l1 = self.calculate_layer1_time()

        total_time = time_l3 + time_l2 + time_l1
        total_static_delay = static_delay_l3 + static_delay_l2 + static_delay_l1
        total_transfer_time = total_time - total_static_delay

        return total_time, {
            'total_transfer_time': total_transfer_time,
            'total_static_delay': total_static_delay
        }

def example_usage():
    #parameter settings
    domain_size = 2 #DP通信域大小
    data_size = 1024 
    total_data_size = data_size * domain_size #总通信量
    tensor_parallel = 2
    node_size = 16/tensor_parallel #单节点内用于dp的rank
    affinity_group_size = 4 #亲合组大小
    roce_bandwidth = 100e9 #RoCE带宽
    hccl_bandwidth = 100e9 #HCCS带宽
    base_static_delay_layer1 = 60e-6 #L1层静态延迟
    base_static_delay_layer2 = 60e-6 #L2层静态延迟

    #创建模型实例
    model = AllGatherModel(total_data_size, domain_size, node_size, affinity_group_size, roce_bandwidth, hccl_bandwidth, base_static_delay_layer1, base_static_delay_layer2, base_static_delay_layer3)

    total_time, breakdown = model.calculate_total_time()
    return total_time, breakdown