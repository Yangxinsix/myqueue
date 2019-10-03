H = 200
h = 100
w = 35

mq = [['M', 10, 45 + h,
       'l', 0, -h + 30],
      ['M', 10, 70,
       'c', 0, h, w, h, w, 0],
      ['M', 10 + w, 70,
       'c', 0, h, w, h, w, 0],
      ['M', 10 + 2 * w, 70,
       'l', 70, 0],
      ['M', 60 + 2 * w, 50,
       'l', 0, h],
      ['M', 60 + 2 * w, 50 + h,
       'c', -50, 0, -50, -50, 0, -50]]

print('<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">')
for i, a in enumerate(mq[::-1]):
    i = 5 - i
    r = 255 - i * 20
    g = 50 + i * 40
    b = 50
    color = f'#{r:02X}{g:02X}{b:02X}'
    xml = []
    xy = False
    for c in a:
        if isinstance(c, str):
            xml.append(c)
            relative = c.islower()
        elif xy:
            if relative:
                xml.append(str(-c))
            else:
                xml.append(str(H - c))
            xy = False
        else:
            xml.append(str(c))
            xy = True

    print('<path d="{}"'.format(' '.join(xml)))
    print('fill="none" '
          'stroke-width="20" '
          'stroke-linecap="round" '
          f'stroke="{color}"/>')

print('</svg>')
