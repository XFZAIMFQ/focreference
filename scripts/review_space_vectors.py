"""Manual technical edit of the space-vectors page after paragraph MT."""
import copy,pathlib,re,sys
from bs4 import BeautifulSoup, NavigableString, Tag

ROOT=pathlib.Path(__file__).resolve().parents[1]
page=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'src/docs/zh-paragraph-candidate/foundations__space-vectors.html'
soup=BeautifulSoup(page.read_text(encoding='utf8'),'html.parser')
blocks=soup.select('main h1, main h2, main h3, main p, main li')
PH=re.compile(r'⟦PH_(\d+)⟧')

def edit(index,template,tag_text=None):
    block=blocks[index]
    tags=[copy.copy(x) for x in block.contents if isinstance(x,Tag)]
    if tag_text:
        for i,value in tag_text.items():tags[i].string=value
    pieces=PH.split(template)
    updated=[]
    for j,piece in enumerate(pieces):
        if j%2==0:
            if piece:updated.append(NavigableString(piece))
        else:updated.append(tags[int(piece)])
    assert sorted(int(x) for x in PH.findall(template))==list(range(len(tags))),(index,len(tags),template)
    block.clear();block.extend(updated)

edit(1,'⟦PH_0⟧一页开篇指出：三相电流可以用一个二维矢量描述。这个结论正确，却不直观。它源于三相绕组的空间布置，值得完整推导一遍；因为变换式和转矩方程中反复出现的 ⟦PH_1⟧ 与 ⟦PH_2⟧ 系数，也正是由此推导出来的。')
edit(4,'电机气隙中的关键量不是电流本身，而是⟦PH_0⟧——电流与匝数的乘积；它推动磁通穿过气隙。',{0:'磁动势'})
edit(5,'实际的定子绕组分布在多个槽中，使其产生的磁动势⟦PH_0⟧，并在绕组轴线上达到峰值：',{0:'沿气隙位置呈正弦分布'})
edit(6,'这里的 ⟦PH_0⟧ 是从 ⟦PH_1⟧ 相绕组轴线起、沿定子内圆周测得的位置角。⟦PH_2⟧ 相和 ⟦PH_3⟧ 相采用相同的绕组结构，空间位置分别偏转 ⟦PH_4⟧。')
edit(9,'只给 ⟦PH_0⟧ 相通入 ⟦PH_1⟧ 形式的电流，则磁动势为：')
edit(14,'三个绕组使反向旋转的分量相互抵消')
edit(22,'三个绕组各自的磁动势峰值为 ⟦PH_0⟧ 时，合成幅值为 ⟦PH_1⟧，而不是 ⟦PH_2⟧。因为三相绕组在空间上相隔 120°，各分量会部分抵消；三个相隔 120°、按 ⟦PH_3⟧ 加权的单位矢量相加，结果恰好是 1.5 倍。')
edit(24,'⟦PH_0⟧公式含有系数 ⟦PH_1⟧：⟦PH_2⟧。')
edit(25,'⟦PH_0⟧公式含有系数 ⟦PH_1⟧：⟦PH_2⟧。')
edit(26,'⟦PH_0⟧的系数是 ⟦PH_1⟧：它恰好抵消前面的 ⟦PH_2⟧，使 ⟦PH_3⟧ 等于相电流峰值。')
edit(27,'⟦PH_0⟧两种约定，只是把这个系数放在不同位置：它总要出现，区别在于写进坐标变换式，还是写进功率方程。')
edit(30,'零序电流⟦PH_0⟧。由此可得到两个重要结论：',{0:'不产生磁场'})
edit(31,'⟦PH_0⟧不会改变电机产生的磁场。对三相占空比同时加入共模项，可将线性调制范围提高 15.5%；电机无法感知这一项，因为它不产生额外磁场。',{0:'SVPWM 的共模注入'})
edit(35,'三相有实际优势：中性点不外接时，三相电流之和为零，⟦PH_0⟧，电机只需三根外接相线；两相系统则需要四根。三相既是能产生旋转磁场的最小相数，⟦PH_1⟧允许各相共用回流路径。译注：英文原文此处称“两根导线可传输三相”，与三相三线制需要三根相线的事实不符。',{0:'任意两相电流就能确定第三相',1:'又'})
edit(36,'因此，把三相变量变换为两个坐标分量不会丢失信息：机器磁场本来就只有两个独立维度，第三相电流可由前两相推得。')
edit(41,'由于合成磁动势⟦PH_0⟧呈正弦分布，两个数就足以完整描述它。它们组成空间矢量，具有明确的物理意义。')
edit(43,'零序电流不产生磁场，因此共模注入不会改变电机磁场，而共模测量偏移也可能被两分流采样方案掩盖。')

page.write_text(str(soup),encoding='utf8')
print('edited',page)
