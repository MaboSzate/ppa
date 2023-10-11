# ppa
bizonytalanság projektmunka

**EXCEL FILE-OK**

- maturity.xlsx: a portfólió elemeinek lejárata, minden napra külön megadva
- nav.xlsx: a ppa eszközeinek nettó összértéke minden napra
- returns.xlsx: a ppa napi hozamai minden napra
- shares.xlsx: a portfólióban szereplő eszközök értékaránya, minden napra külön megadva
- walm.xlsx: a portfólió WAL-jának (ill. WAM-jának - a kettő megegyezik) értéke minden nap (napokban kifejezve)

Amit egyelőre tud:
- betenni állampapírokat, készpénzt, bankbetétet egy alapba
- a napot pörgetve újraárazni, nav-ot számolni
- visszaváltási trajektóriát csinál, készpénzhez hozzáad/elvesz ez alapján
- limiteket megnézi, egy algoritmus tranzakciókat csinál, ha valamelyik limit sérül

Ami hiányzik:
- stressztesztek

Ha lefuttatod a usage.py-t, végigfut a program, kiplotolva, hogy hogy változott az eszközök értéke, a NAV, és a NAV per share. 
Az eszközök a self.assets dataframe-ben vannak. 1-es indexel van a cash, 11-től kezdődő indexel a különböző lejáratú bankbetétek, a kettő közötti indexeléssel az állampapírok. 
A tomorrow függvény pörgeti a napokat, ott látszik, hogy mit nézünk meg minden nap.

A bankbetétünk így működik:
 - egy hét lejáratú lekötött betét
 - lejárat előtt bármikor feltörhető, ekkor nem fizet kamatot
 - ha lejár, alapkamat - 1% éves kamatnak megfelelő kamatot fizet, ekkor ugyanennyit újra berakunk, a kamat megy cash-be
 - a nav számításnál névértéken számoljuk az értékét (tehát a kamatot figyelmen kívül hagyjuk), mivel ennyit fizetne, ha egyből el kéne adni
 - nem nézzük, hogy melyik banknál van: mivel végig 10-20%-a a nav-nak, feltehetjük, hogy diverzifikálni tudjuk úgy, hogy egy intézetben csak max 10%; illetve azt is feltesszük, hogy minden banknál megkapjuk ezt az alapkamat - 1% kamatot 


A check_limits függvénynél látszik, hogy hogy működik a tranzakciókat elvégző algoritmus:
- ha túl kevés a napi lejáratú eszköz, de van sok bankbetét, betör bankbetétet
- ha túl kevés a napi lejáratú eszköz, de nincs sok bankbetét, elad állampapírokat
- ha túl kevés a heti lejáratú eszköz, elad állampípírokat, majd a pénzállomány felét bankbetétbe rakja
- ha kevesebb, mint 6 eszköz van, vesz egy új állampapírt
- ha valami csoda folytán nagyok sok lesz a cash, vesz új állampapírt

