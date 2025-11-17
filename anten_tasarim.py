# anten_tasarim_opt.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import math
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class AntenTasarimUygulamasi:
    def __init__(self, root):
        self.root = root
        self.root.title("Amatör Telsiz Anten Tasarım Uygulaması (Optimizasyonlu)")
        self.root.geometry("1150x800")
        self.root.minsize(900, 650)

        self.c = 299792458.0

        self.bantlar = {
            "160m (1.8-2.0 MHz)": 1.9,
            "80m (3.5-4.0 MHz)": 3.75,
            "40m (7.0-7.3 MHz)": 7.15,
            "30m (10.1-10.15 MHz)": 10.125,
            "20m (14.0-14.35 MHz)": 14.175,
            "17m (18.068-18.168 MHz)": 18.118,
            "15m (21.0-21.45 MHz)": 21.225,
            "12m (24.89-24.99 MHz)": 24.94,
            "10m (28-29.7 MHz)": 28.85,
            "6m (50-54 MHz)": 52.0,
            "2m (144-146 MHz)": 145.0,
            "70cm (430-440 MHz)": 435.0,
            "23cm (1240-1300 MHz)": 1270.0
        }

        self.anten_tipi = tk.StringVar(value="Dipol")
        self.bant_sec = tk.StringVar(value=list(self.bantlar.keys())[10])
        self.frekans = tk.StringVar(value=str(self.bantlar[self.bant_sec.get()]))
        self.vswr = tk.StringVar(value="1.5")
        self.eleman_sayisi = tk.StringVar(value="3")

        self._create_widgets()

    def _create_widgets(self):
        top = ttk.Frame(self.root, padding=(12,10))
        top.pack(side="top", fill="x")

        title = ttk.Label(top, text="Amatör Telsiz Anten Tasarım Uygulaması", font=("Segoe UI", 14, "bold"))
        title.grid(row=0, column=0, columnspan=8, sticky="w", pady=(0,8))

        ttk.Label(top, text="Anten Tipi:").grid(row=1, column=0, sticky="w")
        anten_combo = ttk.Combobox(top, textvariable=self.anten_tipi, values=["Monopol","Dipol","Yagi-Uda"], state="readonly", width=12)
        anten_combo.grid(row=1, column=1, sticky="w", padx=(6,12))
        anten_combo.bind('<<ComboboxSelected>>', lambda e: self._anten_tipi_degisti())

        ttk.Label(top, text="Amatör Bandı:").grid(row=1, column=2, sticky="w")
        bant_combo = ttk.Combobox(top, textvariable=self.bant_sec, values=list(self.bantlar.keys()), state="readonly", width=30)
        bant_combo.grid(row=1, column=3, sticky="w", padx=(6,12))
        bant_combo.bind('<<ComboboxSelected>>', lambda e: self._bant_degisti())

        ttk.Label(top, text="Frekans (MHz):").grid(row=2, column=0, sticky="w", pady=(8,0))
        vcmd_float = (self.root.register(self._validate_float), '%P')
        frekans_entry = ttk.Entry(top, textvariable=self.frekans, validate='key', validatecommand=vcmd_float, width=18)
        frekans_entry.grid(row=2, column=1, sticky="w", padx=(6,12), pady=(8,0))

        ttk.Label(top, text="VSWR Hedefi:").grid(row=2, column=2, sticky="w", pady=(8,0))
        vswr_entry = ttk.Entry(top, textvariable=self.vswr, width=10)
        vswr_entry.grid(row=2, column=3, sticky="w", padx=(6,12), pady=(8,0))

        # Yagi parametreleri
        self.yagi_frame = ttk.LabelFrame(top, text="Yagi-Uda Parametreleri", padding=(8,6))
        self.yagi_frame.grid(row=3, column=0, columnspan=8, sticky="we", pady=(10,0))
        ttk.Label(self.yagi_frame, text="Eleman Sayısı (toplam):").grid(row=0, column=0, sticky="w")
        vcmd_int = (self.root.register(self._validate_int), '%P')
        eleman_entry = ttk.Entry(self.yagi_frame, textvariable=self.eleman_sayisi, validate='key', validatecommand=vcmd_int, width=8)
        eleman_entry.grid(row=0, column=1, sticky="w", padx=(6,12))

        # Butonlar (her durumda görünür)
        btn_frame = ttk.Frame(top)
        btn_frame.grid(row=2, column=4, rowspan=2, sticky="e", padx=(20,0))
        hesapla_btn = ttk.Button(btn_frame, text="Anteni Hesapla", command=self.hesapla)
        hesapla_btn.grid(row=0, column=0, sticky="e", padx=6)
        sifirla_btn = ttk.Button(btn_frame, text="Sıfırla", command=self.sifirla)
        sifirla_btn.grid(row=0, column=1, sticky="e", padx=6)
        about_btn = ttk.Button(btn_frame, text="Hakkında", command=self._hakkinda)
        about_btn.grid(row=0, column=2, sticky="e", padx=6)
        optimize_btn = ttk.Button(btn_frame, text="Yagi Optimize Et", command=self.yagi_optimize_dialog)
        optimize_btn.grid(row=0, column=3, sticky="e", padx=6)

        main_pane = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill="both", expand=True, padx=10, pady=10)

        left_frame = ttk.Frame(main_pane, padding=(8,8))
        left_frame.columnconfigure(0, weight=1)
        main_pane.add(left_frame, weight=1)
        self.sonuc_frame = ttk.LabelFrame(left_frame, text="Tasarım Sonuçları", padding=(8,8))
        self.sonuc_frame.pack(fill="both", expand=False)

        right_frame = ttk.Frame(main_pane, padding=(8,8))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
        main_pane.add(right_frame, weight=2)
        self.gorsel_frame = ttk.LabelFrame(right_frame, text="Anten Görselleştirme", padding=(6,6))
        self.gorsel_frame.pack(fill="both", expand=True)

        self.status_var = tk.StringVar(value="Hazır")
        status = ttk.Label(self.root, textvariable=self.status_var, relief='sunken', anchor='w')
        status.pack(side="bottom", fill="x")

        self._anten_tipi_degisti()

    def _hakkinda(self):
        messagebox.showinfo("Hakkında",
            "Anten Tasarım Uygulaması\nBasit hesaplar ve görselleştirme sağlar.\nOptimizasyon: küçük parametrik tarama (heuristik).")

    def _bant_degisti(self):
        secili = self.bant_sec.get()
        if secili in self.bantlar:
            self.frekans.set(str(self.bantlar[secili]))
            self.status_var.set(f"{secili} seçildi, frekans güncellendi.")

    def _anten_tipi_degisti(self):
        if self.anten_tipi.get() == "Yagi-Uda":
            try:
                self.yagi_frame.grid()
            except Exception:
                pass
            self.status_var.set("Yagi-Uda seçildi.")
        else:
            try:
                self.yagi_frame.grid_remove()
            except Exception:
                pass
            self.status_var.set(f"{self.anten_tipi.get()} seçildi.")

    def _validate_float(self, value):
        if value == "":
            return True
        try:
            float(value)
            return True
        except ValueError:
            return False

    def _validate_int(self, value):
        if value == "":
            return True
        return value.isdigit()

    def sifirla(self):
        self.bant_sec.set(list(self.bantlar.keys())[10])
        self.frekans.set(str(self.bantlar[self.bant_sec.get()]))
        self.vswr.set("1.5")
        self.anten_tipi.set("Dipol")
        self.eleman_sayisi.set("3")
        for w in self.sonuc_frame.winfo_children():
            w.destroy()
        for w in self.gorsel_frame.winfo_children():
            w.destroy()
        self.status_var.set("Sıfırlandı")

    def hesapla(self):
        try:
            frekans_mhz = float(self.frekans.get())
            if frekans_mhz <= 0:
                raise ValueError
        except Exception:
            messagebox.showerror("Hata", "Geçersiz frekans. Lütfen MHz olarak pozitif sayı girin.")
            return

        tip = self.anten_tipi.get()
        try:
            if tip == "Monopol":
                sonuclar = self.monopol_hesapla(frekans_mhz)
            elif tip == "Dipol":
                sonuclar = self.dipol_hesapla(frekans_mhz)
            elif tip == "Yagi-Uda":
                eleman_sayisi = int(self.eleman_sayisi.get())
                if eleman_sayisi < 2:
                    messagebox.showerror("Hata","Yagi-Uda için en az 2 eleman girin.")
                    return
                sonuclar = self.yagi_uda_hesapla(frekans_mhz, eleman_sayisi)
            else:
                messagebox.showerror("Hata","Bilinmeyen anten tipi.")
                return
        except Exception as e:
            messagebox.showerror("Hesaplama Hatası", str(e))
            return

        self.sonuclari_goster(sonuclar)
        self.anten_gorsel_olustur(sonuclar)

    def monopol_hesapla(self, frekans_mhz):
        f = frekans_mhz*1e6
        lam = self.c/f
        uzun = lam/4.0
        return {"tip":"Monopol","frekans":frekans_mhz,"dalga_boyu":lam,"uzunluk":uzun,"empedans":36.5,"kazanc":5.0,"aciklama":"1/4 dalga monopol (yaklaşık)"}

    def dipol_hesapla(self, frekans_mhz):
        f = frekans_mhz*1e6
        lam = self.c/f
        efek = 0.95*(lam/2.0)
        return {"tip":"Dipol","frekans":frekans_mhz,"dalga_boyu":lam,"uzunluk":efek,"empedans":73,"kazanc":2.15,"aciklama":"Yarım dalga dipol (efektif)"}

    def yagi_uda_hesapla(self, frekans_mhz, eleman_sayisi,
                        aktif_factor=0.48, reflektor_factor=1.03,
                        direktor_base_factor=0.46,
                        ref_aktif_factor=0.20, aktif_dir_factor=0.18):
        f = frekans_mhz*1e6
        lam = self.c/f
        aktif = aktif_factor * lam
        reflektor = reflektor_factor * aktif
        direktor_base = direktor_base_factor * lam
        ref_aktif_mesafe = ref_aktif_factor * lam
        aktif_dir_mesafe = aktif_dir_factor * lam
        direktor_sayisi = max(0, eleman_sayisi-2)
        direktorler = []
        for i in range(direktor_sayisi):
            fakt = 1.0 - 0.015*(i+1)
            direktorler.append(direktor_base * fakt)
        elemanlar = {"reflektör":reflektor,"aktif":aktif,"direktörler":direktorler}
        kazanc = 7.0 + 0.8 * direktor_sayisi
        emp = 50
        return {"tip":"Yagi-Uda","frekans":frekans_mhz,"dalga_boyu":lam,"eleman_sayisi":eleman_sayisi,
                "elemanlar":elemanlar,"mesafeler":{"ref_aktif":ref_aktif_mesafe,"aktif_dir":aktif_dir_mesafe},
                "empedans":emp,"kazanc":kazanc,"aciklama":f"{eleman_sayisi} elemanlı Yagi-Uda (yaklaşık)"}

    def sonuclari_goster(self, sonuclar):
        for w in self.sonuc_frame.winfo_children():
            w.destroy()
        row=0
        ttk.Label(self.sonuc_frame, text=f"Anten Tipi: {sonuclar['tip']}", font=("Segoe UI",11,"bold")).grid(row=row,column=0,sticky="w",pady=2); row+=1
        ttk.Label(self.sonuc_frame, text=f"Frekans: {sonuclar['frekans']} MHz").grid(row=row,column=0,sticky="w"); row+=1
        ttk.Label(self.sonuc_frame, text=f"Dalga Boyu: {sonuclar['dalga_boyu']:.3f} m").grid(row=row,column=0,sticky="w"); row+=1
        if sonuclar['tip'] in ("Monopol","Dipol"):
            ttk.Label(self.sonuc_frame, text=f"Anten Uzunluğu: {sonuclar['uzunluk']*100:.2f} cm").grid(row=row,column=0,sticky="w"); row+=1
        if sonuclar['tip']=="Yagi-Uda":
            ttk.Label(self.sonuc_frame, text=f"Eleman Sayısı: {sonuclar['eleman_sayisi']}").grid(row=row,column=0,sticky="w"); row+=1
            ttk.Label(self.sonuc_frame, text="Eleman Uzunlukları (cm):",font=("Segoe UI",10,"bold")).grid(row=row,column=0,sticky="w",pady=(6,2)); row+=1
            ele=sonuclar['elemanlar']
            ttk.Label(self.sonuc_frame, text=f"  Reflektör: {ele['reflektör']*100:.2f} cm").grid(row=row,column=0,sticky="w"); row+=1
            ttk.Label(self.sonuc_frame, text=f"  Aktif: {ele['aktif']*100:.2f} cm").grid(row=row,column=0,sticky="w"); row+=1
            for idx,dlen in enumerate(ele['direktörler'],start=1):
                ttk.Label(self.sonuc_frame, text=f"  Direktör {idx}: {dlen*100:.2f} cm").grid(row=row,column=0,sticky="w"); row+=1
            ttk.Label(self.sonuc_frame, text="Mesafeler (cm):",font=("Segoe UI",10,"bold")).grid(row=row,column=0,sticky="w",pady=(6,2)); row+=1
            ttk.Label(self.sonuc_frame, text=f"  Ref-Aktif: {sonuclar['mesafeler']['ref_aktif']*100:.2f} cm").grid(row=row,column=0,sticky="w"); row+=1
            ttk.Label(self.sonuc_frame, text=f"  Aktif-Direktör aralığı: {sonuclar['mesafeler']['aktif_dir']*100:.2f} cm").grid(row=row,column=0,sticky="w"); row+=1
        ttk.Label(self.sonuc_frame, text=f"Empedans (yaklaşık): {sonuclar['empedans']} Ω").grid(row=row,column=0,sticky="w",pady=(6,2)); row+=1
        ttk.Label(self.sonuc_frame, text=f"Kazanç (yaklaşık): {sonuclar['kazanc']:.2f} dBi").grid(row=row,column=0,sticky="w"); row+=1
        ttk.Label(self.sonuc_frame, text=f"Açıklama: {sonuclar.get('aciklama','')}").grid(row=row,column=0,sticky="w",pady=(6,2)); row+=1
        self.status_var.set("Hesaplama tamamlandı.")

    def anten_gorsel_olustur(self, sonuclar):
        for w in self.gorsel_frame.winfo_children():
            w.destroy()
        fig, ax = plt.subplots(figsize=(8,5), constrained_layout=True)
        tip=sonuclar['tip']
        if tip=="Monopol":
            self._monopol_gorsel(ax,sonuclar)
        elif tip=="Dipol":
            self._dipol_gorsel(ax,sonuclar)
        elif tip=="Yagi-Uda":
            self._yagi_gorsel(ax,sonuclar)
        ax.set_xlabel("Uzunluk (cm)")
        ax.set_ylabel("Yükseklik (cm) (gösterim sıkıştırıldı)")
        ax.grid(True, alpha=0.35)
        ax.set_title(f"{sonuclar['tip']} Anten Tasarımı - {sonuclar['frekans']} MHz")
        canvas = FigureCanvasTkAgg(fig, self.gorsel_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _monopol_gorsel(self, ax, sonuclar):
        uzun_cm = sonuclar['uzunluk']*100
        ax.plot([0,0],[0,uzun_cm],linewidth=5)
        ax.plot([-40,40],[0,0],linewidth=2)
        ax.scatter([0],[0],s=50,c='red',zorder=5)
        ax.set_xlim(-60,60)
        ax.set_ylim(-20, max(uzun_cm+20,50))

    def _dipol_gorsel(self, ax, sonuclar):
        toplam_cm = sonuclar['uzunluk']*100
        yari = toplam_cm/2.0
        ax.plot([-yari,0],[0,0],linewidth=5)
        ax.plot([0,yari],[0,0],linewidth=5)
        ax.scatter([0],[0],s=50,c='red')
        ax.set_xlim(-yari*1.3,yari*1.3)
        ax.set_ylim(-max(10,yari*0.2), max(10,yari*0.2))

    def _yagi_gorsel(self, ax, sonuclar):
        ele = sonuclar['elemanlar']
        ref_aktif = sonuclar['mesafeler']['ref_aktif']*100
        aktif_dir = sonuclar['mesafeler']['aktif_dir']*100
        pozisyon = []
        poz_ref = 0.0
        poz_aktif = poz_ref + ref_aktif
        pozisyon.append(("Reflektör", poz_ref, ele['reflektör']*100))
        pozisyon.append(("Aktif", poz_aktif, ele['aktif']*100))
        for i,dlen in enumerate(ele['direktörler']):
            poz = poz_aktif + (i+1)*aktif_dir
            pozisyon.append((f"Direktör {i+1}", poz, dlen*100))
        xs = [p[1] for p in pozisyon]
        lengths = [p[2] for p in pozisyon]
        minx, maxx = min(xs)-20, max(xs)+20
        max_x_range = maxx - minx if (maxx - minx) > 0 else 1.0
        max_len = max(lengths) if lengths else 1.0
        # Görsel sıkıştırma faktörü: dikey uzunlukları yatay ölçeğe göre dengeler
        desired_vspan_fraction = 0.25  # dikey gösterim yatayın %25'i kadar olsun
        scale_factor = 1.0
        if max_len > max_x_range * desired_vspan_fraction:
            scale_factor = max_len / (max_x_range * desired_vspan_fraction)
        # çizim: boom
        ax.plot([minx, maxx], [0,0], color='black', linewidth=2)
        # elemanları çiz, fakat yükseklikleri scale_factor ile küçült
        colors = {'Reflektör':'tab:red','Aktif':'tab:blue'}
        for label, xpos, length in pozisyon:
            hy = (length/2.0) / scale_factor
            color = colors.get(label.split()[0],'tab:green')
            ax.plot([xpos,xpos], [-hy, hy], linewidth=4, color=color)
            # etiketleri biraz üstte göster; gerçek uzunluğu da yaz
            ax.text(xpos, hy + 5, f"{label}\n({length:.1f} cm)", ha='center', fontsize=9)
        ax.scatter([poz_aktif],[0],s=60,c='red',zorder=5)
        ax.set_xlim(minx-10, maxx+10)
        # Y eksenini sıkıştırılmış değerlerle ayarla; kullanıcıya not ekle
        vpad = max([ (l/2.0)/scale_factor for l in lengths ]) if lengths else 10
        ax.set_ylim(-vpad*1.6, vpad*1.6)
        ax.text(minx+10, -vpad*1.4, f"(DİKKAT: Dikey gösterim sıkıştırıldı; etiketler gerçek uzunlukları gösterir)",
                fontsize=8, color='gray')

    # Basit Yagi optimizasyon dialog + grid-search
    def yagi_optimize_dialog(self):
        # Parametreleri soru kutuları ile al
        try:
            eleman = int(self.eleman_sayisi.get())
            if eleman < 2:
                messagebox.showerror("Hata","Eleman sayısı en az 2 olmalı.")
                return
        except Exception:
            messagebox.showerror("Hata","Geçersiz eleman sayısı.")
            return
        # Basit parametre aralıklarını sor
        # Direktör faktör aralığı (örn 0.42 - 0.50)
        d_min = simpledialog.askfloat("Optimize - Direktör uzunluk faktörü (min)",
                                      "Direktör uzunluk faktörü min (lambda çarpanı, örn 0.42):", initialvalue=0.44, minvalue=0.30, maxvalue=0.60)
        if d_min is None: return
        d_max = simpledialog.askfloat("Optimize - Direktör uzunluk faktörü (max)",
                                      "Direktör uzunluk faktörü max (lambda çarpanı, örn 0.49):", initialvalue=0.48, minvalue=d_min, maxvalue=0.9)
        if d_max is None: return
        s_min = simpledialog.askfloat("Optimize - Aktif-Direktör aralığı çarpanı (min)",
                                      "Aralık çarpanı min (ör. 0.14):", initialvalue=0.14, minvalue=0.08, maxvalue=0.4)
        if s_min is None: return
        s_max = simpledialog.askfloat("Optimize - Aktif-Direktör aralığı çarpanı (max)",
                                      "Aralık çarpanı max (ör. 0.22):", initialvalue=0.20, minvalue=s_min, maxvalue=0.6)
        if s_max is None: return

        # grid çözümü: az sayıda adım ile hızlı tarama
        steps = 6
        d_vals = np.linspace(d_min, d_max, steps)
        s_vals = np.linspace(s_min, s_max, steps)
        # ayrıca aktif_factor yakın etrafı küçük tarama
        af_vals = np.linspace(0.46, 0.50, 3)

        best = None
        best_params = None
        self.status_var.set("Optimizasyon başladı...")
        self.root.update_idletasks()

        # Basit heuristik: kazanç = 7 + 0.8*ndirector - spacing_penalty - length_penalty
        for af in af_vals:
            for dv in d_vals:
                for sv in s_vals:
                    # model hesap
                    son = self.yagi_uda_hesapla(float(self.frekans.get()), eleman,
                                                aktif_factor=af,
                                                reflektor_factor=1.03,
                                                direktor_base_factor=dv,
                                                ref_aktif_factor=sv,
                                                aktif_dir_factor=sv)
                    nd = max(0, eleman-2)
                    gain = son['kazanc']
                    # penalty'ler: ideal spacing ~0.18*lambda, ideal direktor_base ~0.46*lambda
                    lam = son['dalga_boyu']
                    ideal_spacing = 0.18*lam
                    spacing = son['mesafeler']['aktif_dir']
                    spacing_pen = 5.0 * abs(spacing - ideal_spacing) / (ideal_spacing + 1e-9)
                    direktor_base = son['elemanlar']['direktörler'][0] if son['elemanlar']['direktörler'] else 0.46*lam
                    ideal_db = 0.46*lam
                    length_pen = 6.0 * abs(direktor_base - ideal_db) / (ideal_db + 1e-9)
                    score = gain - spacing_pen - length_pen
                    if (best is None) or (score > best):
                        best = score
                        best_params = {"aktif_factor":af, "direktor_base_factor":dv, "spacing_factor":sv, "score":score, "result":son}

        if best_params is None:
            messagebox.showinfo("Sonuç", "Optimizasyon sonuç üretmedi.")
            self.status_var.set("Optimizasyon iptal edildi.")
            return

        # Sonuç göster
        res = best_params['result']
        score = best_params['score']
        msg = (f"En iyi parametreler (basit tarama):\n"
               f"Aktif faktör: {best_params['aktif_factor']:.3f}\n"
               f"Direktör base faktör: {best_params['direktor_base_factor']:.3f}\n"
               f"Aralık faktörü: {best_params['spacing_factor']:.3f}\n\n"
               f"Tahmini kazanç (heuristik): {res['kazanc']:.2f} dBi\n"
               f"Skor: {score:.2f}\n\n"
               "Bulunan parametrelerle son anten tasarımını görüntülemek ister misiniz?")
        if messagebox.askyesno("Optimizasyon Sonucu", msg):
            # Eleman sayısını ve hesap parametrelerini kullanarak tekrar hesapla/göster
            yeni = self.yagi_uda_hesapla(float(self.frekans.get()), res['eleman_sayisi'],
                                         aktif_factor=best_params['aktif_factor'],
                                         direktor_base_factor=best_params['direktor_base_factor'],
                                         ref_aktif_factor=best_params['spacing_factor'],
                                         aktif_dir_factor=best_params['spacing_factor'])
            self.sonuclari_goster(yeni)
            self.anten_gorsel_olustur(yeni)
            self.status_var.set("Optimizasyon tamamlandı ve sonuç gösterildi.")
        else:
            self.status_var.set("Optimizasyon tamamlandı.")

def main():
    root = tk.Tk()
    app = AntenTasarimUygulamasi(root)
    root.mainloop()

if __name__ == "__main__":
    

    main()
