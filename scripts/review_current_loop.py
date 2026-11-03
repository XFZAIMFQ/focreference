"""Manual wording and technical review of the current-loop focus page."""
import copy,pathlib,re,sys
from bs4 import BeautifulSoup,NavigableString,Tag
ROOT=pathlib.Path(__file__).resolve().parents[1]
page=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'src/docs/zh-paragraph-candidate/control__current-loop.html'
soup=BeautifulSoup(page.read_text(encoding='utf8'),'html.parser')
blocks=soup.select('main h1, main h2, main h3, main p, main li')
ph=re.compile(r'⟦PH_(\d+)⟧')
edits={
19:('那条淡淡的虚线，是关闭所有非理想因素后同一驱动器的响应。实线与虚线之间的差距⟦PH_0⟧这些非理想因素造成的损失。',{0:'就是'}),
25:('⟦PH_0⟧ 在 2000 rpm、死区时间为 2% 时，⟦PH_1⟧ 的纹波约为 0.6 A。将电流给定从 12 A 降至 3 A，纹波⟦PH_2⟧约为 0.6 A。死区时间造成的误差固定为 0.96 V，即 48 V 母线电压的 2%；它在 12 A 时占目标电压的 3.5%，在 3 A 时占 7.2%。工作点降低时，这项误差不会同比减小，因此低速时死区时间补偿尤其重要。',{}),
28:('观察 ⟦PH_0⟧ 曲线。启用反算时，撤销电流给定后约 300 µs，电流便开始回落；关闭反算后，积分器已经对一个不可能突破的限幅累积了 11 ms，结果是⟦PH_1⟧：记录结束时电流仍在流动，相电流仍以全幅值摆动，桥臂也仍处于饱和状态。对比实线和虚线，故障一目了然。',{1:'电流始终不回落'}),
30:('⟦PH_0⟧ 大惯量不是为了让演示更戏剧化，而是让演示⟦PH_1⟧。裸转子的惯量仅为 12 g·cm²，足够轻，可能在积分器发生积分饱和之前就加速离开饱和区。实际负载通常更重，因此积分饱和是真实负载中必须处理的问题。',{1:'符合实际'}),
33:('非凸极电机的曲线几乎完全符合 ⟦PH_0⟧，这也符合预期。但基准凸极电机不同：角度误差为 10° 时，转矩甚至⟦PH_1⟧完全对齐时的转矩。',{1:'高于'}),
36:('由此得到两个方向相反的结论。好消息是，凸极电机比教科书公式预示的更能容忍小角度误差；坏消息是，⟦PH_0⟧。角度误差达 20° 时，转矩仅下降 2%，与测量噪声难以区分，但同时已有 3.6 A 的非期望电流使电机发热并削弱磁场。',{0:'仅看转矩读数无法发现角度误差'}),
38:('这也是最大转矩电流比（MTPA）的出发点。如果负的 ⟦PH_0⟧ 可以额外产生转矩，问题就不再是“怎样让 ⟦PH_1⟧ 保持为零”，而是“在给定 ⟦PH_2⟧ 时，最优的 ⟦PH_3⟧ 是多少”。后文会继续讨论。',{}),
41:('如果不加补偿，这三项都会在控制器看来成为随转速增大的扰动。因此，只在静止状态下整定的环路，会随着电机升速而逐渐变差。加入前馈补偿只需两次乘法运算：',{}),
51:('当 ⟦PH_0⟧ 时，系统会稳定在 ⟦PH_1⟧：积分器恰好停在饱和边界，一旦限幅解除就能立即恢复。若将 ⟦PH_2⟧ 设得太小，积分器仍会继续累积，只是速度较慢；抗积分饱和项便形同虚设。这类错误很隐蔽：代码看似正确，相关项也存在，但问题只在持续饱和时出现。',{}),
54:('两个轴不能各自独立限幅。逆变器将它们组成的矢量⟦PH_0⟧限制在 ⟦PH_1⟧ 以内。因此应先计算两轴输出，再对矢量统一限幅，最后根据实际输出对⟦PH_2⟧积分器进行反算。',{}),
65:('死区时间和角度误差都会降低驱动性能，⟦PH_0⟧让控制器报告异常。要查找角度误差，应观察 ⟦PH_1⟧；转矩变化不足以作为线索，在凸极电机上尤其如此。',{0:'却未必'}),
}
for index,(template,labels) in edits.items():
    block=blocks[index];tags=[copy.copy(x) for x in block.contents if isinstance(x,Tag)]
    assert sorted(int(x) for x in ph.findall(template))==list(range(len(tags))),(index,len(tags))
    for i,label in labels.items():tags[i].string=label
    pieces=ph.split(template);new=[]
    for j,piece in enumerate(pieces):
        if j%2==0:
            if piece:new.append(NavigableString(piece))
        else:new.append(tags[int(piece)])
    block.clear();block.extend(new)
page.write_text(str(soup),encoding='utf8')
print('edited',len(edits),'current-loop blocks')
