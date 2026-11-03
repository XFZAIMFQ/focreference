"""Edit paragraphs for which the MT model could not preserve inline tags."""
import copy,pathlib,re,sys
from bs4 import BeautifulSoup,NavigableString,Tag

ROOT=pathlib.Path(__file__).resolve().parents[1]
root=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'src/docs/zh-paragraph-candidate'
sel='main p, main li, main h2, main h3, main figcaption, main th, main td'
ph=re.compile(r'⟦PH_(\d+)⟧')
edits={
('control__current-loop.html',64):('⟦PH_0⟧ 前馈应在输出限幅⟦PH_1⟧加入，而不是之后。若在限幅之后才加入前馈，控制器的输出会饱和，但抗积分饱和机制无法感知，因此不会启动；这个问题只会在前馈量较大的高速工况下显现。',{1:'之前'}),
('control__sampled-time.html',60):('⟦PH_0⟧ 离散化不只影响相位，还有一个更容易注意到的影响：在穿越频率处，前向欧拉法的增益约⟦PH_1⟧，后向欧拉法约偏高 5%，因此穿越频率也会发生相近幅度的偏移。Tustin 法的偏差不到 0.1%。',{1:'偏低 5%'}),
('control__sensorless.html',94):('⟦PH_0⟧ 从 3600 rpm 降到 600 rpm 时，角度误差一直约为 4°；而在 600 至 400 rpm 之间，误差突然急剧增大。它没有一个可供逐步调节的平缓退化过程，而是先正常工作，随后突然失效。',{0:'磁链观测器在失效前的表现基本平稳：'}),
('control__sensorless.html',97):('⟦PH_0⟧ 加入 1.5% 的死区时间，观察中速区间：在 1800 rpm 时，磁链观测器误差只从 4.0° 增至 4.6°，因为 0.72 V 的误差与 6.4 V 的反电动势相比很小。问题在于死区时间误差是⟦PH_1⟧，而反电动势会随转速下降而减小；低速时两者就会接近。死区时间页与本页讨论的低速问题，其实是同一个问题。',{}),
('foundations__clarke-park.html',21):('两种约定本身都没有错；不加说明地混用才是常见错误。这样会使转矩常数偏差 22%，而系统仍⟦PH_0⟧工作正常。',{}),
('foundations__clarke-park.html',59):('Park 反变换是 Park 变换的转置，因为旋转矩阵是正交的。但在幅值不变的约定下，Clarke 反变换⟦PH_0⟧正变换的转置：正变换中的 ⟦PH_1⟧ 系数必须被抵消。只有在功率不变的约定下，逆矩阵才是转置矩阵。复制代码前，应先确认它采用了哪种约定。',{0:'不是'}),
('foundations__clarke-park.html',69):('接下来讨论 ⟦PH_0⟧ 和 ⟦PH_1⟧ 在电机中究竟⟦PH_2⟧什么变化：转矩如何产生、凸极性有什么作用，以及为什么 ⟦PH_3⟧ 通常是合适的默认值，又在何时不再适用。',{2:'带来'}),
('foundations__per-unit.html',24):('现在各参数的量级都在 1 附近。这并非形式上的好处，而是能让错误的数值⟦PH_0⟧不合理。标幺值电阻为 0.505，显然像一台正常电机；若为 8.0，则明显异常。以国际单位制表示时，若不了解电机，仅凭 0.35 Ω 无从判断。',{0:'显得'}),
('implementation__architecture.html',23):('⟦PH_0⟧ 依次采集电流、执行 Clarke 与 Park 变换、运行两个电流 PI、解耦、逆 Park 变换、调制并写入占空比。仅做这些；不要在中断里分配内存、记录日志或等待。实测这部分耗时约 12 µs，而 PWM 周期为 62.5 µs；这是在该硬件上⟦PH_1⟧的数值，不是模型估计。',{0:'快速路径：每个 PWM 周期在中断服务程序中执行一次。',1:'测得'}),
('implementation__timing.html',77):('与相位裕度不同，这种误差⟦PH_0⟧可以补偿，而且代价很低：一次乘法加一次加法。应当进行补偿。',{0:'确实'}),
('inverter__bridge.html',35):('当高侧开关导通、电流从桥臂流向绕组时，电流流过高侧晶体管；当高侧开关仍导通而电流⟦PH_0⟧桥臂时，它只能经该晶体管的反并联二极管回流。两种情况下桥臂电压相同，因此前文的平均模型可以忽略这一区别。',{0:'流入'}),
('inverter__six-step.html',4):('转子继续旋转时，电流方向却保持不变。因此，电流方向与它⟦PH_0⟧指向的理想方向——即超前转子磁链四分之一周——之间的夹角，从扇区开始时的 +30° 逐渐经过中点的 0°，到结束时变为 −30°；随后跳变，重新开始。',{0:'本应'}),
('inverter__six-step.html',25):('这三个电压极限构成⟦PH_0⟧，相邻两者的比值都是 ⟦PH_1⟧。因此，⟦PH_2⟧相较普通 SPWM 增加的 15.5%，与从空间矢量调制升至六步换相时再次获得的 15.5% ⟦PH_3⟧。从普通正弦调制到六步换相，总电压提高约三分之一。',{}),
('inverter__svpwm.html',76):('⟦PH_0⟧ V1 为 ⟦PH_1⟧，V2 为 ⟦PH_2⟧，V3 为 ⟦PH_3⟧；沿六边形依次走，相邻矢量的开关状态只差一位。这不是为了编号整齐；这种编码⟦PH_4⟧相邻状态之间只需切换一个桥臂。若两个状态不相邻，过渡时就得同时切换两个桥臂。',{4:'使得'}),
('machine__dq-model.html',86):('⟦PH_0⟧，因为铁心逐渐饱和。因此，要求精度的量产驱动器通常使用在测功机上实测的二维（2-D）查找表，而不是只用两个常数。',{0:'随着电流增大，L_d 和 L_q 都会减小'}),
('machine__dq-model.html',88):('⟦PH_0⟧ 一组自洽的参数还应满足功率平衡，这是一个现成的校验方法。在 1500 rpm、10 A 时，模型吸收 ⟦PH_1⟧ W 的电功率，向电机轴输出 80.1 W，绕组损耗为 52.5 W；80.1 + 52.5 恰好等于 132.6。这里的 ⟦PH_2⟧ 是幅值不变约定下的功率系数，转矩方程中也有同样的系数，其来源可追溯到⟦PH_3⟧页的三相绕组合成磁动势。若实测功率不平衡，应先检查这个系数。',{}),
('machine__field-weakening.html',53):('⟦PH_0⟧ 注意最后三行：电流限制作用于电流⟦PH_1⟧的总幅值。随着 ⟦PH_2⟧ 变得更负，留给 ⟦PH_3⟧ 的余量便会减小；转矩下降是这种几何约束的结果，不必另行下达降转矩指令。若对各轴分别限幅，总电流可能达到预期上限的 ⟦PH_4⟧ 倍。这与⟦PH_5⟧和⟦PH_6⟧页讨论的限幅错误相同：共享的余量必须共同限制。',{}),
('machine__field-weakening.html',56):('这就是⟦PH_0⟧，属于安全问题，而非性能问题。因此，牵引电机通常设计成特征电流处于额定电流⟦PH_1⟧：能抵消自身磁链的电机，其短路电流也有上界；故障时主动短接三相便可能成为安全响应。',{1:'以内'}),
('sensing__position.html',15):('因此必须测定偏移角。通常的做法是沿控制器⟦PH_0⟧的 d 轴方向通入电流，让转子转到该方向并锁定。',{0:'认为是'}),
}

by_file={}
for (name,index),(template,label_overrides) in edits.items():
    if name not in by_file:
        page=root/name
        by_file[name]=(page,BeautifulSoup(page.read_text(encoding='utf8'),'html.parser'))
    page,soup=by_file[name]
    block=soup.select(sel)[index]
    tags=[copy.copy(x) for x in block.contents if isinstance(x,Tag)]
    assert sorted(int(x) for x in ph.findall(template))==list(range(len(tags))),(name,index,len(tags))
    for i,value in label_overrides.items():tags[i].string=value
    pieces=ph.split(template);new=[]
    for j,piece in enumerate(pieces):
        if j%2==0:
            if piece:new.append(NavigableString(piece))
        else:new.append(tags[int(piece)])
    block.clear();block.extend(new)
for page,soup in by_file.values():page.write_text(str(soup),encoding='utf8')
print('edited',len(edits),'paragraphs in',len(by_file),'pages')
