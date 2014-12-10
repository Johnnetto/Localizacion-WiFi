from kivy.app import App
from kivy.uix.scatter import Scatter
from kivy.uix.button import Button
from kivy.logger import Logger
from kivy.graphics import Color, Ellipse
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.uix.popup import Popup
from kivy.uix.label import Label

import androidhelper, time, sys
import sqlite3 as lite
import location



class Scatter2(Scatter):

#
#              cur.executemany("INSERT INTO Cars VALUES(?, ?, ?)", cars)
#              cur.execute("SELECT * FROM Cars")
#              rows = cur.fetchall()
#              cur.execute("UPDATE Cars SET Price=? WHERE Id=?", (uPrice, uId))
#

    def __init__(self):

        super(Scatter2,self).__init__()
        self.lastScan = None
        self.aps = None
        self.isLongTouch = False
        self.droid = androidhelper.Android()
        self.droid.wifiStartScan()
        self.location = location.Location()
        Clock.schedule_interval(self.scanTimer, 5)
        
        self.con = lite.connect('tfinal.db')
        cur = self.con.cursor()
        cur.execute("SELECT * FROM Ubicacion")
        rows = cur.fetchall()

        for row in rows:
            id_ubicacion = row[0]
            x = float(row[1])
            y = float(row[2])
            cur2 = self.con.cursor()
            cur2.execute("SELECT * FROM HuellaParcial WHERE IDUbicacion = '%i'" % (id_ubicacion))
            rows2 = cur2.fetchall()
            fp = dict()

            for row2 in rows2:
                mac = row2[1]
                intensidad = float(row2[2])
                fp[mac] = intensidad

            place = location.Place(x,y,fp)
            self.location.add_place(place)

            self.draw_circle(x, y, (0, 1, 0))



        
    # Detecta los touch downs e inicia un timer de un segundo    
    def on_touch_down(self, touch):
        self.touchDown = self.to_window(touch.x, touch.y)
        self.isLongTouch = False
        Clock.schedule_once(self.longTouchTimer, 1)
        return super(Scatter2, self).on_touch_down(touch)
        
    # Si el timer vence lo deja marcado
    def longTouchTimer(self, dt):
        self.isLongTouch = True
            
    # Si se levanta el dedo en el mismo lugar y el timer esta vencido
    # entonces consideramos que es un long touch
    def on_touch_up(self, touch):
        wTouch = self.to_window(touch.x, touch.y)
        if wTouch[0] == self.touchDown[0] and wTouch[1] == self.touchDown[1] and self.isLongTouch:
            print "Llamando a onLongTouch"
            self.isLongTouch = False
            self.onLongTouch(touch)
        return super(Scatter2, self).on_touch_up(touch)
            
    def onLongTouch(self, touch):
        p = self.to_local(touch.x, touch.y)
        self.lastScan = self.scanResults()


        with self.con:
            cur = self.con.cursor()
            cur.execute("INSERT INTO Ubicacion(X, Y, Z, IDPiso) VALUES(?,?,0,1)", (p[0], p[1]))
            idubicacion = cur.lastrowid

            for point in self.aps:
                cur.execute("INSERT INTO HuellaParcial(MAC, Intensidad, IDUbicacion) VALUES (?,?,?)", (point["bssid"], point["level"], idubicacion))

            self.con.commit()

        f = open("fingerprints", "a")
        f.write("{0:.3f},{1:.3f}{2}\n".format(p[0], p[1], self.lastScan))
        f.close()

        self.draw_circle(p[0], p[1], (1,1,0))

    def draw_circle(self, x, y, color):
        with self.canvas:
            Color(*color)
            Ellipse(pos=(x - 30 / 2, y - 30 / 2), size=(30, 30))
        
    # Escanea las redes en background, cada 10 segundos; en mi telefono
    # nunca refresca las redes...
    def scanTimer(self, dt):
        scan = self.scanResults()
        if not scan == self.lastScan:
            self.droid.vibrate()
        if self.droid.wifiStartScan():
            print "Escaneando redes..."
        else:
            print "ERROR: el escaneo de redes fallo."
        return True
        
    def scanResults(self):
        ap = self.droid.wifiGetScanResults()
        self.aps = ap.result
        s = ""
        for point in self.aps:
            s += ", " + point["bssid"] + ", " + str(point["level"])
        return s


    def ubicar(self, btndonde):

        if self.aps is None:
            return

        fp = dict()
        for point in self.aps:
            fp[point["bssid"]] = float(point["level"])
        place = self.location.find_closest_place(fp)

        if place is not None:
            self.draw_circle(place.x, place.y, (1, 0, 0))
        else:
            popup = Popup(title='Error',
                          content=Label(text='Lugar no encontrado'),
                          size_hint=(None, None), size=(200, 200))





class PlanoApp(App):
    def build(self):
        parent = Scatter2()
        btndonde = Button(size=(400,150),
                          text='Donde estoy?',
                      background_color=(0, 0, 1, 1),  # List of
                                                      # rgba components
                      font_size=30)
        btndonde.bind(on_press=parent.ubicar)
        parent.add_widget(btndonde)
        return parent



if __name__ == "__main__":
    PlanoApp().run()
