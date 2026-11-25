"""Genera diagramas vectoriales y lista de cableado desde una única tabla."""
from pathlib import Path
from html import escape as esc
import json
import re

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'montaje'
OUT.mkdir(parents=True, exist_ok=True)
COLORS = {'3V3':'#c026d3','GND':'#334155','5V':'#dc2626','TEMP':'#ca8a04',
          'SDA':'#059669','SCL':'#2563eb','TRIG':'#ea580c','ECHO5':'#9333ea',
          'ECHO3':'#0891b2','BUTTON':'#7c3aed'}
# G:A1 = grupo 1 contado desde el primer agujero izquierdo, línea A.
# P:A2 = coordenada impresa A2 de la protoboard pequeña.
WIRES = [
 ('01','ESP:3V3','G:A1','3V3','H–M'),
 ('02','ESP:GND','G:A5','GND','H–M'),
 ('03','ESP:VIN','G:A10','5V','H–M'),
 ('04','TZT:VCC','G:B1','3V3','H–M'),
 ('05','TZT:GND','G:B5','GND','H–M'),
 ('06','TZT:DAT','G:A15','TEMP','H–M'),
 ('07','MPU:VCC','G:C1','3V3','H–M'),
 ('08','MPU:GND','G:C5','GND','H–M'),
 ('09','MPU:AD0','G:D5','GND','H–M'),
 ('10','MPU:SDA','ESP:D21','SDA','H–H'),
 ('11','MPU:SCL','ESP:D22','SCL','H–H'),
 ('12','G:E5','G:A6','GND','M–M'),
 ('13','HC:VCC','G:B10','5V','H–M'),
 ('14','HC:GND','G:B6','GND','H–M'),
 ('15','HC:TRIG','ESP:D18','TRIG','H–H'),
 ('16','HC:ECHO','P:A5','ECHO5','H–M'),
 ('17','G:C6','P:A2','GND','M–M'),
 ('18','P:B10','ESP:D19','ECHO3','M–H'),
 ('19','P:C2','P:J20','GND','M–M'),
 ('20','P:A20','ESP:D27','BUTTON','M–H'),
 ('21','ESP:D4','G:B15','TEMP','H–M'),
]
RESISTORS = [('R1a','P:E5','P:E10',2000),('R1b','P:C5','P:C10',2000),
             ('R2','P:D10','P:D2',2000),('R3a','G:E1','G:E8',2000),
             ('R3b','G:D8','G:E15',2000)]
TOP_PINS = ['D23','D22','TX0','RX0','D21','D19','D18','D5','TX2','RX2','D4','D2','D15','GND','3V3']
BOTTOM_PINS = ['EN','VP','VN','D34','D35','D32','D33','D25','D26','D27','D14','D12','D13','GND','VIN']

def validate():
    source=(ROOT/'src/main.cpp').read_text(encoding='utf-8')
    for pin,value in [('TEMP_PIN',4),('TRIG_PIN',18),('ECHO_PIN',19),('BUTTON_PIN',27)]:
        assert re.search(rf'\b{pin}\s*=\s*{value}\b',source), f'GPIO distinto en firmware: {pin}'
    assert re.search(r'Wire\.begin\(\s*21\s*,\s*22\s*\)',source)
    assert len(WIRES)==21 and len(RESISTORS)==5
    kinds=[k.replace('M–H','H–M') for _,_,_,_,k in WIRES]
    assert kinds.count('H–M')==15 and kinds.count('H–H')==3 and kinds.count('M–M')==3
    parent = {}
    def group(p):
        if p.startswith(('G:', 'P:')) and p[2] in 'ABCDEFGHIJ':
            b,c,r = p[0],p[2],p[3:]
            return f'{b}:{"L" if c in "ABCDE" else "R"}{r}'
        return p
    def find(p):
        p=group(p)
        parent.setdefault(p,p)
        if parent[p]!=p: parent[p]=find(parent[p])
        return parent[p]
    def union(a,b): parent[find(a)]=find(b)
    used={}
    for name,a,b,net,kind in WIRES:
        for p in (a,b):
            assert p not in used, f'Agujero ocupado dos veces: {p}'
            used[p]=name
        union(a,b)
    for name,a,b,value in RESISTORS:
        for p in (a,b):
            assert p not in used, f'Agujero ocupado dos veces: {p}'
            used[p]=name
    # Patas del pulsador: verificar esta topología por continuidad antes del montaje.
    for p in ['P:E20','P:F20','P:E22','P:F22']:
        assert p not in used
    union('P:E20','P:E22');union('P:F20','P:F22')
    rails=[find(x) for x in ['ESP:3V3','ESP:GND','ESP:VIN']]
    assert len(set(rails))==3, 'Cortocircuito de alimentación'
    for sensor,power in [('TZT:VCC','ESP:3V3'),('MPU:VCC','ESP:3V3'),('HC:VCC','ESP:VIN')]:
        assert find(sensor)==find(power)
    for pin in ['TZT:GND','MPU:GND','MPU:AD0','HC:GND','P:D2','P:F20']:
        assert find(pin)==find('ESP:GND')
    for a,b in [('TZT:DAT','ESP:D4'),('MPU:SDA','ESP:D21'),('MPU:SCL','ESP:D22'),('HC:TRIG','ESP:D18'),('P:E20','ESP:D27')]:
        assert find(a)==find(b)
    assert find('HC:ECHO')==find('P:E5')
    assert find('ESP:D19')==find('P:E10')==find('P:D10')
    assert find('HC:ECHO')!=find('ESP:D19')
    assert find('G:E1')==find('ESP:3V3') and find('G:E15')==find('ESP:D4')
    assert find('G:E8')==find('G:D8') and find('G:E8') not in rails
    assert find('P:C5')==find('P:E5') and find('P:C10')==find('P:E10')
    print('PASS: 21 cables y 5 resistencias de 2 kohm; sin agujeros duplicados ni cortos de alimentacion; GPIO y divisor correctos.')

def text(x,y,t,size=18,fill='#0f172a',weight='normal',anchor='start'):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" text-anchor="{anchor}">{esc(str(t))}</text>'
def rect(x,y,w,h,fill='#fff',stroke='#cbd5e1',rx=12):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}"/>'
def line(x,y,u,v,color,width=3):
    return f'<path d="M{x},{y} L{u},{v}" stroke="{color}" stroke-width="{width}" fill="none"/>'
def svgfile(name,w,h,parts):
    s=f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="Segoe UI,Arial,sans-serif"><rect width="100%" height="100%" fill="#f1f5f9"/>'+''.join(parts)+'</svg>'
    (OUT/name).write_text(s,encoding='utf-8')

def main_diagram():
    s=[text(40,50,'Montaje real · ESP32 + dos protoboards',30,weight='bold'),
       text(40,82,'Los números 01–21 identifican cables. Mantén el USB desconectado durante el montaje.',18),
       rect(40,110,1320,275,'#0f172a','#0f172a'),text(65,145,'ESP32 · misma orientación de tu foto: antena a la izquierda y USB a la derecha',20,'#fff','bold')]
    active={'D4':'TEMP','D18':'TRIG','D19':'ECHO3','D21':'SDA','D22':'SCL','D27':'BUTTON','3V3':'3V3','VIN':'5V','GND':'GND'}
    for pins,y in [(TOP_PINS,195),(BOTTOM_PINS,335)]:
        for i,pin in enumerate(pins):
            x=90+i*78; color=COLORS.get(active.get(pin,''),'#64748b')
            # Se usa el GND inferior, junto a VIN. El GND superior queda libre.
            if pin=='GND' and y==195: color='#64748b'
            s += [rect(x-28,y-25,61,43,color,color,5),text(x+3,y+3,pin,16,'#fff','bold','middle')]
    s += [rect(71,232,160,55,'#334155','#64748b',4),text(151,266,'ANTENA',18,'#fff',anchor='middle'),
          rect(1185,232,140,55,'#94a3b8','#94a3b8',4),text(1255,266,'USB →',20,'#0f172a','bold','middle')]
    cards=[('TZT · adaptador de la sonda',40,420,['04','05','06','21']),
           ('MPU-6050 · SY-104',720,420,['07','08','09','10','11']),
           ('HC-SR04',40,740,['13','14','15','16','18']),
           ('Distribución y pulsador',720,740,['01','02','03','12','17','19','20'])]
    lookup={w[0]:w for w in WIRES}
    for title,x,y,ids in cards:
        s += [rect(x,y,640,290),text(x+22,y+34,title,23,weight='bold')]
        for i,ident in enumerate(ids):
            _,a,b,net,kind=lookup[ident]; yy=y+70+i*29
            s += [rect(x+20,yy-17,39,24,COLORS[net],COLORS[net],5),text(x+39,yy,ident,14,'#fff','bold','middle'),text(x+72,yy,f'{a}  →  {b}',18)]
    s += [rect(40,1060,1320,180,'#fff7ed','#fdba74'),text(62,1095,'Divisor obligatorio en la protoboard pequeña',24,weight='bold'),
          text(62,1134,'R1a 2 kΩ: E5–E10 ∥ R1b 2 kΩ: C5–C10 → equivalente 1 kΩ → fila 10 → D19',21),
          text(62,1170,'Nodo fila 10 — [R2 2 kΩ: D10–D2] — GND. ECHO no va directo al ESP32.',21),
          text(62,1207,'R3a 2 kΩ: G:E1–G:E8 + R3b 2 kΩ: G:D8–G:E15 → serie 4 kΩ entre 3V3 y DAT.',21)]
    s += [text(40,1290,'G = grande (coordenadas propias, ver su plano). P = pequeña (coordenadas impresas).',19),
          text(40,1323,'Sonda confirmada: amarillo → DAT · rojo → VCC · negro → GND. Alimentación TZT: 3,3 V.',19),
          text(40,1356,'MPU: XDA, XCL e INT sin conectar. ESP32 y módulos se unen con Dupont; no se insertan en estas rejillas.',18)]
    svgfile('01-conexiones.svg',1400,1400,s)

def occupancy(board):
    d={}
    for ident,a,b,net,kind in WIRES:
        for p in [a,b]:
            if p.startswith(board+':'): d[p]=(ident,COLORS[net])
    for name,a,b,val in RESISTORS:
        for p in [a,b]:
            if p.startswith(board+':'): d[p]=(name,'#92400e')
    return d

def large_diagram():
    s=[text(40,48,'G · Protoboard grande',30,weight='bold'),text(40,82,'Colócala horizontal como en tu foto: A arriba, J abajo. Usa únicamente el bloque A–E.',19),
       text(40,112,'G1 = primer grupo de 5 agujeros del extremo izquierdo. G2 = siguiente, etc.',19),
       text(40,142,'Esta numeración propia se cuenta desde el primer agujero; no se basa en los números impresos.',18,'#b45309','bold')]
    x0,y0,dx,dy=105,235,48,40
    s += [rect(55,180,1210,540,'#fafaf9','#cbd5e1')]
    for n in range(1,25):
        x=x0+(n-1)*dx
        s.append(text(x,208,str(n),15,anchor='middle'))
        for j,c in enumerate('ABCDEFGHIJ'):
            y=y0+j*dy+(45 if j>=5 else 0)
            if j==0: s.append(text(x,195,'',12))
            p=f'G:{c}{n}'; found=occupancy('G').get(p)
            # Columna de 5 contactos conectados internamente.
            if j in (0,5): s.append(line(x,y,x,y+4*dy,'#e2e8f0',10))
            s.append(f'<circle cx="{x}" cy="{y}" r="{14 if found else 4}" fill="{found[1] if found else "#94a3b8"}"/>')
            if found: s.append(text(x,y+5,found[0],12,'#fff','bold','middle'))
    for j,c in enumerate('ABCDEFGHIJ'):
        s.append(text(75,y0+j*dy+(45 if j>=5 else 0)+6,c,18,weight='bold'))
    # Cada resistencia toca únicamente sus dos agujeros; G8 une D8 y E8.
    y=y0+4*dy;x1=x0;xm=x0+7*dx;x2=x0+14*dx
    s += [line(x1,y+17,x1,y+42,'#92400e'),line(x1,y+42,xm,y+42,'#92400e'),line(xm,y+42,xm,y+17,'#92400e'),
          rect((x1+xm)/2-65,y+25,130,32,'#fef3c7','#92400e',5),text((x1+xm)/2,y+48,'R3a · 2 kΩ',17,'#78350f','bold','middle'),
          line(xm+14,y-dy,xm+30,y-dy,'#92400e'),line(xm+30,y-dy,xm+30,y+42,'#92400e'),line(xm+30,y+42,x2,y+42,'#92400e'),line(x2,y+42,x2,y+17,'#92400e'),
          rect((xm+x2)/2-65,y+25,130,32,'#fef3c7','#92400e',5),text((xm+x2)/2,y+48,'R3b · 2 kΩ',17,'#78350f','bold','middle')]
    s += [text(1280,280,'→',27),text(1280,315,'Resto',17),text(1280,341,'libre',17)]
    notes=[('G1 · 3,3 V','A1 cable 01 · B1 cable 04 · C1 cable 07 · E1 pata R3a'),
           ('G5 · GND','A5 cable 02 · B5 cable 05 · C5 cable 08 · D5 cable 09 · E5 cable 12'),
           ('G6 · extensión GND','A6 cable 12 · B6 cable 14 · C6 cable 17'),
           ('G10 · 5 V','A10 cable 03 · B10 cable 13'),
           ('G8 · punto intermedio del pull-up','E8 pata R3a · D8 pata R3b · resto del grupo libre'),
           ('G15 · DAT','A15 cable 06 · B15 cable 21 · E15 pata R3b')]
    for i,(t,n) in enumerate(notes):
        y=760+i*74;s += [text(55,y,t,22,weight='bold'),text(55,y+31,n,19)]
    s += [text(55,1225,'El puente 12 une E5 con A6. No unas G1 (3V3) con G10 (5V).',20,'#b91c1c','bold'),
          text(55,1260,'No se usan los carriles laterales +/−. No hace falta puentear sus posibles cortes.',19),
          text(55,1295,'Cada A…E del mismo grupo está unido. F…J está separado por el canal central.',19),
          text(55,1330,'Los números dentro de los contactos son los IDs de cable, no números de agujero.',19)]
    svgfile('02-protoboard-grande.svg',1400,1370,s)

def small_diagram():
    s=[text(35,45,'P · Protoboard pequeña',29,weight='bold'),text(35,78,'Orientación de tu foto: A–J arriba; fila 1 arriba y 30 abajo.',18)]
    xmap={c:100+i*38+(35 if i>=5 else 0) for i,c in enumerate('ABCDEFGHIJ')}
    ymap={r:140+(r-1)*25 for r in range(1,31)}
    s.append(rect(55,95,490,840,'#fafaf9'))
    for c,x in xmap.items(): s.append(text(x,122,c,17,weight='bold',anchor='middle'))
    occ=occupancy('P')
    for r,y in ymap.items():
        s.append(text(72,y+5,r,14,anchor='middle'))
        for start,end in [('A','E'),('F','J')]:s.append(line(xmap[start],y,xmap[end],y,'#e2e8f0',9))
        for c,x in xmap.items():
            found=occ.get(f'P:{c}{r}')
            s.append(f'<circle cx="{x}" cy="{y}" r="{12 if found else 3.5}" fill="{found[1] if found else "#94a3b8"}"/>')
            if found:s.append(text(x,y+4,found[0],11,'#fff','bold','middle'))
    for name,a,b,value in [r for r in RESISTORS if r[1].startswith('P:')]:
        c1,r1=a[2],int(a[3:]);c2,r2=b[2],int(b[3:]);x=xmap[c1];y1=ymap[r1];y2=ymap[r2]
        s += [line(x,y1,x, y2,'#92400e',4),rect(x-13,(y1+y2)/2-23,26,46,'#fef3c7','#92400e',4)]
    s += [text(595,150,'Todas las resistencias: 2 kΩ',23,weight='bold'),text(595,187,'R1a: E5 ↔ E10',21),
          text(595,223,'R1b: C5 ↔ C10',21),text(595,259,'R2: D10 ↔ D2',21),text(595,295,'R1a ∥ R1b = 1 kΩ equivalente',19),
          text(595,325,'Entrada ECHO: fila 5, A–E',20,'#9333ea','bold'),
          text(595,359,'Salida a D19: fila 10, A–E',20,'#0891b2','bold'),
          text(595,393,'GND: fila 2, A–E',20,'#334155','bold')]
    bx1,bx2=xmap['E'],xmap['F'];by1,by2=ymap[20],ymap[22]
    s += [rect(bx1-9,by1-8,bx2-bx1+18,by2-by1+16,'#cbd5e1','#334155',4),
          f'<circle cx="{(bx1+bx2)/2}" cy="{(by1+by2)/2}" r="17" fill="#334155"/>']
    for c,r in [('E',20),('F',20),('E',22),('F',22)]:
        s.append(f'<circle cx="{xmap[c]}" cy="{ymap[r]}" r="5" fill="#eab308" stroke="#0f172a"/>')
    s += [text(595,510,'Pulsador · posición propuesta',23,weight='bold'),text(595,546,'Patas: E20, F20, E22, F22.',20),
          text(595,581,'A20 → cable 20 → ESP:D27',20),text(595,616,'J20 → cable 19 → GND',20),
          text(595,670,'Verifica sin alimentación:',21,'#b45309','bold'),
          text(595,707,'E20–E22: continuidad permanente.',18),text(595,741,'F20–F22: continuidad permanente.',18),
          text(595,775,'E20–F20: solo al pulsar.',18),text(595,821,'Si no coincide, no conectes el pulsador:',18,'#b45309'),
          text(595,852,'identifica sus pares o gíralo y repite.',18,'#b45309'),
          text(595,900,'A–E unidos por fila. F–J unidos por fila.',18),text(595,932,'Los dos lados están separados.',18),
          text(35,985,'El esquema del pulsador requiere esa continuidad y que sus patas encajen sin forzarlas.',18),
          text(35,1020,'Si el cuerpo no encaja, usa los mismos dos contactos mediante cables externos.',18),
          text(35,1055,'Deja los carriles laterales libres. Nunca puentes E10 con E5: anularías R1.',19,'#b91c1c','bold')]
    svgfile('03-protoboard-pequena.svg',1140,1100,s)

def docs():
    color_names={'3V3':'fucsia (3,3 V)','GND':'negro','5V':'rojo (5 V)','TEMP':'amarillo','SDA':'verde','SCL':'azul','TRIG':'naranja','ECHO5':'morado','ECHO3':'cian','BUTTON':'violeta'}
    intro='''# Montaje real, cable por cable

Preparado con tus fotos de `images/` y los GPIO del firmware que pasó la simulación.

## Cómo colocar las piezas

- **ESP32 fuera de las protoboards**, sobre una superficie aislante. La orientación del dibujo coincide con tu foto: antena a la izquierda, conector USB a la derecha. Los nombres se leen en la serigrafía; D21 significa GPIO21. Usa el GND de la misma hilera que VIN, inmediatamente a su lado.
- **Grande (G)** horizontal, A arriba y J abajo, como en la foto. Solo usamos su bloque A–E. Para evitar ambigüedad de los números impresos, los grupos **G1, G2… se cuentan desde el primer agujero del extremo izquierdo**. `G:A5` es el quinto agujero de la línea A contado desde la izquierda, no necesariamente el número impreso 5. A–E del mismo grupo están conectados internamente.
- **Pequeña (P)** vertical, como en tu foto, A–J arriba, fila 1 arriba. Aquí **sí usamos los números y letras impresos**. `P:E10` significa E10. A–E de una fila están unidos; F–J de esa fila forman otro grupo separado.
- TZT, MPU y HC-SR04 quedan fuera de la rejilla y se conectan con cables a sus pines macho. Esto deja libres sus etiquetas y evita asumir una separación mecánica de pines.
- Retira el pulsador que aparece suelto en la grande. Solo se insertará en la pequeña después de comprobar sus contactos, como se explica abajo. Los carriles laterales +/− quedan sin usar: no dependemos de sus cortes internos.

## Diagramas

1. [Conexiones y pines del ESP32](01-conexiones.svg)
2. [Cada agujero de la protoboard grande](02-protoboard-grande.svg)
3. [Divisor y pulsador en la protoboard pequeña](03-protoboard-pequena.svg)

Los IDs **01–21** del dibujo corresponden a la tabla. Los colores son una recomendación para los cables nuevos; los nombres de los terminales mandan sobre el color.

Los planos muestran las conexiones y la posición de cada contacto; no son plantillas a escala 1:1 para perforar o cortar cables.

## Antes de conectar USB

Necesitas **15 cables hembra–macho, 3 hembra–hembra y 3 macho–macho**, más **cinco resistencias de 2 kΩ**. R1a y R1b forman 1 kΩ en paralelo; R3a y R3b forman 4 kΩ en serie. H = extremo hembra que recibe un pin del módulo; M = extremo macho para un agujero. No uses cables pelados apoyados sobre los pines del ESP32.

La sonda se conecta al borne verde del TZT según tu confirmación: **amarillo → DAT, rojo → VCC y negro → GND**. Conecta después los pines macho DAT/VCC/GND del adaptador según la tabla. El adaptador se alimenta con **3,3 V**. No conectes otra fuente externa junto con USB.

El montaje incluye R3a y R3b en serie para garantizar un pull-up externo de 4 kΩ. El adaptador parece tener una resistencia SMD de 4,7 kΩ: si se confirma entre DAT y VCC, puedes omitir ambas resistencias externas. Si mantienes el pull-up interno de 4,7 kΩ y el externo de 4 kΩ, el equivalente es aproximadamente 2,16 kΩ, admisible para este bus corto a 3,3 V. No retires componentes SMD. [Detalle de la adaptación](SOLO-2K.md).

## Los 21 cables

| ID | Extremo 1 | Extremo 2 | Color sugerido | Terminales |
|---|---|---|---|---|
'''
    table='\n'.join(f'| {i} | `{a}` | `{b}` | {color_names[n]} | {k} |' for i,a,b,n,k in WIRES)
    end='''

`ESP` = ESP32; `TZT` = adaptador de temperatura; `MPU` = MPU-6050; `HC` = HC-SR04. El cable 12 prolonga GND de G5 a G6; el 17 lleva GND a la pequeña. No hay un cable adicional entre nodos que ya están unidos por las tiras internas de la protoboard.

## Las cinco resistencias de 2 kΩ

| Pieza | Valor | Primera pata | Segunda pata | Función |
|---|---|---|---|---|
| R1a | 2 kΩ | P:E5 | P:E10 | En paralelo con R1b |
| R1b | 2 kΩ | P:C5 | P:C10 | En paralelo con R1a: equivalente 1 kΩ |
| R2 | 2 kΩ | P:D10 | P:D2 | Del nodo de lectura a GND |
| R3a | 2 kΩ | G:E1 | G:E8 | Primer tramo del pull-up |
| R3b | 2 kΩ | G:D8 | G:E15 | En serie con R3a: equivalente 4 kΩ |

Las resistencias no tienen polaridad. Aísla las patas desnudas que puedan tocar otras conexiones. Los únicos contactos eléctricos de cada resistencia son sus dos extremos indicados. G:D8 y G:E8 están unidos internamente y forman el punto intermedio del pull-up; el resto de G8 queda libre.

Con resistencias de cuatro bandas: 2 kΩ = rojo/negro/rojo, más su banda de tolerancia. Confirma el valor con multímetro si el código de bandas es distinto. Usa tolerancia del 5 % o mejor.

El recorrido de ECHO es:

```text
HC ECHO ── cable 16 ── P:A5 [misma tira que E5]
                                 │
                       R1a 2 kΩ ∥ R1b 2 kΩ
                                 │
P:B10 ── cable 18 ── ESP D19 ── nodo de la fila 10, A–E
                                 │
                              R2 2 kΩ
                                 │
                         fila 2, A–E ── GND
```

R1a entra en E10, R1b en C10 y R2 en D10: comparten el nodo de la fila 10 a través de la protoboard, sin ocupar el mismo agujero. Con 5 V en ECHO, el divisor entrega aproximadamente 3,33 V a D19. **No conectes ECHO directamente a D19 y no puentes R1a/R1b.**

## Pulsador: posición y comprobación necesaria

La foto muestra un pulsador de cuatro patas, pero no permite comprobar cuáles están unidas internamente. Por eso esta colocación depende de una comprobación real, no de deducirlo por el plástico.

1. Sin USB ni otra alimentación, verifica con multímetro dos pares que estén unidos permanentemente. Entre un par y el otro debe haber continuidad únicamente al pulsar.
2. Colócalo cruzando el canal central de la pequeña, con patas en **E20, F20, E22 y F22**, si encaja sin doblarlas a la fuerza. Debe cumplirse: E20–E22 unidos siempre; F20–F22 unidos siempre; E20–F20 unidos solo al pulsar. Si no coincide, identifica los pares y cambia la orientación; no alimentes hasta que coincida.
3. El cable **20** entra en **A20** y va a **ESP D27**. El **19** entra en **J20** y viene de **P:C2 (GND)**. El firmware ya usa `INPUT_PULLUP`; no necesita resistencia externa en el pulsador.
4. Si no encaja mecánicamente, deja el pulsador fuera y usa cables a un contacto de cada par: uno a A20 y otro a J20. El circuito eléctrico es el mismo.

En el MPU quedan **XDA, XCL e INT libres**. AD0 sí va a GND para usar la dirección I²C 0x68. No se conectan otros pines del ESP32.

## Orden de montaje y primera alimentación

1. Mantén USB desconectado. Coloca R1a, R1b, R2, R3a y R3b. Las cinco son de 2 kΩ. Comprueba sus valores.
2. Conecta los cables 01–05, 07–09, 12–14 y 17 (alimentación y tierras). Verifica que G1, G5/G6 y G10 estén separados: 3,3 V, GND y 5 V respectivamente.
3. Conecta los cables 06, 10, 11, 15, 16, 18 y 21 (señales).
4. Comprueba los contactos del pulsador, colócalo y conecta 19 y 20.
5. Revisa la sonda: DAT/amarillo, VCC/rojo, GND/negro, según tu confirmación. Comprueba que los tornillos sujeten el conductor y que no haya hilos sueltos.
6. Sin alimentación, comprueba que no exista un cortocircuito permanente entre alimentación y GND. Comprueba las uniones de las protoboards y el divisor según el dibujo.
7. Conecta únicamente USB al ESP32. Mide aproximadamente 3,3 V entre G1 y G5/G6 y 5 V entre G10 y G5/G6. Si VIN no entrega aproximadamente 5 V con USB, desconecta y revisa la variante de la placa antes de alimentar el HC-SR04.
8. El ESP32 aislado fue detectado en COM3 y ya se cargó el firmware. Si necesitas cargarlo otra vez: `powershell -ExecutionPolicy Bypass -File scripts/upload.ps1 -Port COM3`, comprobando antes que siga siendo ese puerto. Después abre `scripts/monitor.ps1` y conecta Java a ese COM.

Este documento define el cableado; no afirma que el montaje físico ya esté comprobado. La topología de las tiras de las protoboards y los contactos del pulsador se verifican sin alimentación. El firmware ya fue compilado y probado en Wokwi.

## Referencias

- Fotos propias: `images/ESP32.jpg`, `TZT-DS1820.jpg`, `MPU-6050-FRONT.jpg`, `MPU-6050-BACK.jpg`, `HC-SR04-FRONT.jpg` y ambas protoboards.
- [DS18B20: alimentación, pull-up y niveles de bus](https://www.analog.com/media/en/technical-documentation/data-sheets/DS18B20.pdf).
- [ESP32: características eléctricas y GPIO](https://documentation.espressif.com/esp32_datasheet_en.html).
- [HC-SR04: VCC, TRIG, ECHO y GND](https://docs.wokwi.com/parts/wokwi-hc-sr04).
'''
    (OUT/'MONTAJE.md').write_text(intro+table+end,encoding='utf-8')
    rows=''.join(f'<tr><td><input type="checkbox" aria-label="Cable {i} instalado"></td><td><b>{i}</b></td><td>{esc(a)}</td><td>{esc(b)}</td><td><span style="color:{COLORS[n]}">●</span> {esc(color_names[n])}</td><td>{k}</td></tr>' for i,a,b,n,k in WIRES)
    html='''<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Montaje real · Monitor ESP32</title><style>
body{font:17px/1.6 system-ui,sans-serif;background:#f1f5f9;color:#0f172a;margin:0}main{max-width:1400px;margin:auto;padding:32px}h1{font-size:36px;line-height:1.2}section{background:white;padding:24px;margin:24px 0;border-radius:16px}a{color:#1d4ed8}img.diagram{width:100%;height:auto}table{width:100%;border-collapse:collapse;font-size:16px}th,td{text-align:left;padding:10px;border-bottom:1px solid #cbd5e1}th{background:#f8fafc}input{width:21px;height:21px}tr:has(input:checked){background:#dcfce7}aside{padding:18px 24px;border-left:5px solid #eab308;background:#fffbeb}.photos{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}.photos img{width:100%;max-height:350px;object-fit:contain}figure{margin:0}button{padding:9px 20px;border:0;border-radius:8px;background:#1d4ed8;color:white;font:inherit;cursor:pointer}@media print{main{padding:0}body{background:white}section{break-before:page;padding:0}section:first-of-type{break-before:auto}button{display:none}.photos{grid-template-columns:repeat(2,1fr)}}
</style><main><h1>Montaje real: cada cable y cada contacto</h1><p>ESP32 · TZT DS18x20 · MPU-6050 · HC-SR04 · pulsador. Preparado con tus fotografías y los GPIO del firmware probado.</p>
<p><a href="MONTAJE.md">Instrucciones completas y comprobaciones</a> · <a href="#cables">Lista de 21 cables</a> · <a href="#fotos">Fotos originales</a></p>
<aside><b>Antes de alimentar:</b> monta con USB desconectado. Sonda según tu confirmación: amarillo→DAT, rojo→VCC, negro→GND. No conectes ECHO directamente al ESP32. La posición del pulsador requiere comprobar sus pares por continuidad.</aside>
<section><h2>1. Puertos y conexiones</h2><p><b>Versión actual: cinco resistencias de 2 kΩ, mismos 21 cables y mismo firmware.</b> ESP32 y módulos fuera de las protoboards. H = hembra; M = macho. Necesitas 15 H–M, 3 H–H y 3 M–M. <a href="SOLO-2K.md">Detalle de las resistencias</a> · <a href="04-resistencias-2k.png">Plano resumido</a>.</p><a href="01-conexiones.svg"><img class="diagram" src="01-conexiones.svg" alt="Cada pin de los módulos y su destino"></a></section>
<section><h2>2. Protoboard grande</h2><p><b>Numeración propia:</b> G1 es el primer grupo de agujeros del extremo izquierdo; G2 el siguiente. Cuenta agujeros desde el borde, no uses el número impreso como sustituto. Solo usamos A–E. No se usan los carriles +/−.</p><a href="02-protoboard-grande.svg"><img class="diagram" src="02-protoboard-grande.svg" alt="Agujeros y contactos de la protoboard grande"></a></section>
<section><h2>3. Protoboard pequeña</h2><p>Usa sus coordenadas impresas A–J y 1–30. Confirma los contactos del pulsador antes de colocarlo. Si las patas no encajan, usa cables hacia los mismos dos nodos.</p><a href="03-protoboard-pequena.svg"><img class="diagram" src="03-protoboard-pequena.svg" alt="Resistencias de ECHO y pulsador en la pequeña"></a></section>
<section id="cables"><h2>4. Lista de montaje</h2><p>Marca cada cable al colocarlo. Las marcas se conservan en este navegador.</p><table><thead><tr><th>Hecho</th><th>ID</th><th>Extremo 1</th><th>Extremo 2</th><th>Color sugerido</th><th>Terminales</th></tr></thead><tbody>'''+rows+'''</tbody></table><h3>Cinco resistencias, todas de 2 kΩ</h3><table><thead><tr><th>Pieza</th><th>Valor</th><th>Primera pata</th><th>Segunda pata</th></tr></thead><tbody>'''+''.join(f'<tr><td>{name}</td><td>2 kΩ</td><td>{a}</td><td>{b}</td></tr>' for name,a,b,value in RESISTORS)+'''</tbody></table><p>R1a y R1b en paralelo equivalen a 1 kΩ. R3a y R3b en serie equivalen a 4 kΩ. R2 se mantiene. Si confirmas un pull-up interno de 4,7 kΩ entre DAT y VCC del adaptador, puedes omitir R3a/R3b. <a href="MONTAJE.md">Ver instrucciones, pulsador y primera alimentación</a>.</p></section>
<section id="fotos"><h2>5. Referencias del hardware real</h2><div class="photos">'''
    for f in ['ESP32.jpg','TZT-DS1820.jpg','MPU-6050-FRONT.jpg','MPU-6050-BACK.jpg','HC-SR04-FRONT.jpg','PROTOBOARD-GRANDE.jpg','PROTOBOARD-PEQUEÑA.jpg']:
        html+=f'<figure><a href="../../images/{esc(f)}"><img src="../../images/{esc(f)}" alt="{esc(f)}"></a><figcaption>{esc(f)}</figcaption></figure>'
    html+='''</div></section><p><button onclick="window.print()">Imprimir guía</button></p><p>Comprueba el montaje sin alimentación antes de conectar USB. Las comprobaciones físicas siguen pendientes.</p></main><script>document.querySelectorAll('input[type=checkbox]').forEach((e,i)=>{const k='esp32-montaje-v1-'+i;try{e.checked=localStorage.getItem(k)==='1'}catch{}e.addEventListener('change',()=>{try{localStorage.setItem(k,e.checked?'1':'0')}catch{}})});</script></html>'''
    (OUT/'index.html').write_text(html,encoding='utf-8')
    (OUT/'cableado.json').write_text(json.dumps({'wires':WIRES,'resistors':RESISTORS},ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':
    validate();main_diagram();large_diagram();small_diagram();docs()
