"""Manual wording review of the per-unit focus page."""
import copy,pathlib,re,sys
from bs4 import BeautifulSoup,NavigableString,Tag
ROOT=pathlib.Path(__file__).resolve().parents[1]
page=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'src/docs/zh-paragraph-candidate/foundations__per-unit.html'
soup=BeautifulSoup(page.read_text(encoding='utf8'),'html.parser')
blocks=soup.select('main h1, main h2, main h3, main p, main li')
ph=re.compile(r'⟦PH_(\d+)⟧')
edits={
1:'实际交付的驱动器都要做两项数值换算，许多教程却略过了它们。两者是独立概念，通常结合使用：国际单位制的数值不便于控制器统一处理，也不便于定点运算。',
9:'取另一台电机：电阻和电感都是原电机的四倍，磁链是两倍；再把它的基准电流设为原电机的一半、基准电压设为两倍。这样得到的标幺值描述与原电机⟦PH_0⟧。本站的测试验证了这一点，数值误差低于 1e-12。',
12:'换回国际单位制后，时间常数是 600 µs，恰好等于 ⟦PH_0⟧，符合预期。',
16:'⟦PH_0⟧ 表示小数点后有 ⟦PH_1⟧ 位。下面两个性质尤其重要：',
26:'解决办法是留出一位表示整数部分。16 位 Q14 格式的可表示范围为 ⟦PH_0⟧，分辨率为 2.44 mA：精度减半，余量加倍，额定值处不再溢出。对于 32 位处理器，这个问题基本消失；Q24 的范围可达 ⟦PH_1⟧ 标幺值，分辨率为 0.002 mA。',
34:'缩放不会凭空增加精度',
49:'接下来可以先读⟦PH_0⟧；如果已经读过，就前往⟦PH_1⟧，了解如何控制这个矢量。',
}
for index,template in edits.items():
    block=blocks[index];tags=[copy.copy(x) for x in block.contents if isinstance(x,Tag)]
    assert sorted(int(x) for x in ph.findall(template))==list(range(len(tags))),(index,len(tags))
    parts=ph.split(template);new=[]
    for j,x in enumerate(parts):
        if j%2==0:
            if x:new.append(NavigableString(x))
        else:new.append(tags[int(x)])
    block.clear();block.extend(new)
page.write_text(str(soup),encoding='utf8')
print('edited',len(edits),'per-unit blocks')
