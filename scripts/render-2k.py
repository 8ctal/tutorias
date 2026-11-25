"""Plano vectorial de los cinco resistores de 2 kΩ, sin mover cables."""
import importlib.util
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('wiring',root/'scripts/generate-wiring.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
t,r,l=w.text,w.rect,w.line
s=[t(35,48,'Solo resistencias de 2 kΩ · mismos 21 cables',30,weight='bold'),
   t(35,84,'Desconecta USB. Retira R1 y R3 originales; conserva R2. No cambies GPIO ni firmware.',19),
   r(35,110,1130,440),t(60,148,'P · pequeña · coordenadas impresas',25,weight='bold')]
x={c:110+i*65 for i,c in enumerate('ABCDE')};y={2:230,5:340,10:470}
for c,xx in x.items():s.append(t(xx,194,c,19,weight='bold',anchor='middle'))
for row,yy in y.items():
 s += [t(65,yy+6,row,20,weight='bold'),l(x['A'],yy,x['E'],yy,'#cbd5e1',12)]
 for c,xx in x.items():s.append(f'<circle cx="{xx}" cy="{yy}" r="6" fill="#64748b"/>')
for c,a,b,label in [('C',5,10,'R1b'),('E',5,10,'R1a'),('D',2,10,'R2')]:
 xx=x[c];yy=(y[a]+y[b])/2
 s += [l(xx,y[a],xx,y[b],'#92400e',4),r(xx-19,yy-22,38,44,'#fef3c7','#92400e',4),t(xx,yy+5,label,13,weight='bold',anchor='middle')]
for c,row,ident,color in [('A',5,'16','#9333ea'),('B',10,'18','#0891b2'),('A',2,'17','#334155'),('C',2,'19','#334155')]:
 s += [f'<circle cx="{x[c]}" cy="{y[row]}" r="15" fill="{color}"/>',t(x[c],y[row]+5,ident,13,'#fff','bold','middle')]
for i,txt in enumerate(['R1a: E5 ↔ E10 · 2 kΩ','R1b: C5 ↔ C10 · 2 kΩ','R2: D10 ↔ D2 · 2 kΩ','R1a ∥ R1b = 1 kΩ','ECHO → 1 kΩ → D19 → 2 kΩ → GND','Salida ≈ 3,33 V para ECHO de 5 V']):
 s.append(t(510,220+i*47,txt,22,weight='bold' if i in (3,5) else 'normal'))
s += [r(35,580,1130,365),t(60,620,'G · grande · grupos contados desde el primer agujero izquierdo',23,weight='bold')]
gx={1:160,8:390,15:620};gy={'A':690,'B':725,'C':760,'D':795,'E':830}
for col,xx in gx.items():
 s += [t(xx,661,f'G{col}',19,weight='bold',anchor='middle'),l(xx,gy['A'],xx,gy['E'],'#cbd5e1',12)]
 for c,yy in gy.items():s.append(f'<circle cx="{xx}" cy="{yy}" r="6" fill="#64748b"/>')
for c,yy in gy.items():s.append(t(105,yy+6,c,18,weight='bold'))
# Solo los extremos tocan los agujeros indicados.
s += [l(160,830,160,880,'#92400e'),l(160,880,390,880,'#92400e'),l(390,880,390,830,'#92400e'),
      r(225,863,105,33,'#fef3c7','#92400e',5),t(277,886,'R3a 2 kΩ',16,weight='bold',anchor='middle'),
      l(390,795,445,795,'#92400e'),l(445,795,445,880,'#92400e'),l(445,880,620,880,'#92400e'),l(620,880,620,830,'#92400e'),
      r(475,863,115,33,'#fef3c7','#92400e',5),t(532,886,'R3b 2 kΩ',16,weight='bold',anchor='middle'),
      t(715,698,'R3a: E1 ↔ E8 · 2 kΩ',22),t(715,744,'R3b: D8 ↔ E15 · 2 kΩ',22),t(715,790,'D8 y E8 unidos por dentro.',20),t(715,836,'Serie: 2 kΩ + 2 kΩ = 4 kΩ',20,weight='bold'),
      t(55,998,'Total: 5 resistencias de 2 kΩ. Los cables y sus agujeros permanecen iguales.',22,weight='bold'),
      t(55,1035,'Los dibujos muestran solo los grupos usados. No unas las dos patas de una resistencia en la misma tira.',18),
      t(55,1072,'El pulsador y los módulos conservan las conexiones de la guía original.',19)]
w.svgfile('04-resistencias-2k.svg',1200,1110,s)
# Equivalentes y márgenes nominales del diseño, sin afirmar una prueba física.
parallel=1/(1/2000+1/2000)
assert parallel==1000 and 2000+2000==4000
voltage=5*2000/(parallel+2000)
assert 0.75*3.3 < voltage < 3.6
assert 3.3/(1/(1/4000+1/4700)) < .004
resistors=[('R1a','P:E5','P:E10',2000),('R1b','P:C5','P:C10',2000),
           ('R2','P:D10','P:D2',2000),('R3a','G:E1','G:E8',2000),('R3b','G:D8','G:E15',2000)]
occupied={p for _,a,b,_,_ in w.WIRES for p in (a,b)}
for name,a,b,value in resistors:
 for endpoint in (a,b):
  assert endpoint not in occupied, 'Contacto ocupado: '+endpoint
  occupied.add(endpoint)
(w.OUT/'cableado-2k.json').write_text(json.dumps({'wires':w.WIRES,'resistors':resistors},ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS: paralelo 1 kohm; serie 4 kohm; ECHO nominal %.3f V; pull-up dentro de corriente de hundimiento DS18B20.' % voltage)
