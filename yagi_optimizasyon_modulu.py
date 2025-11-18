# yagi_optimizasyon_modulu.py
"""
Basit Yagi Optimizasyon Modülü
Bu modül, temel Yagi-Uda tasarımı için grid search tabanlı optimizasyon yapar.
Çap (radius/diameter) parametresini kullanarak empedans ve SWR tahminini günceller.
"""
import numpy as np
import math

# Işık hızı (m/s)
C = 299792458.0

# Temel kazanç tahmini (empirik, kaba bir model)
def estimate_gain(num_elements, spacing_factor):
    # Spacing factor lambdanın çarpanı (örneğin 0.18)
    base_gain = 2.15 # Dipol kazancı
    gain_increase = 0.8 * (num_elements - 1)
    spacing_penalty = 10 * (spacing_factor - 0.18)**2 
    gain = base_gain + gain_increase - spacing_penalty
    return max(3.0, gain) 

# Empedans tahmini (radius_m parametresi eklendi)
def estimate_impedance(ref_len, act_len, dir_len, spacing, wavelength, radius_m): 
    # Tüm uzunluklar metre cinsinden
    # Kalın elemanlar empedansı düşürür, bant genişliğini artırır.
    
    # L/a (Dalga boyu/Yarıçap) oranı
    ratio_lambda_radius = wavelength / radius_m
    
    # Basitleştirilmiş Logaritmik Çap Düzeltmesi
    # Empedans (Z) üzerinde kalınlığın etkisini gösteren kaba bir model
    # Z ~ 60 * ln(2L/a)
    # Bizim durumumuzda, empedansın 50 Ohm civarında kalınlık arttıkça hafifçe düştüğünü varsayalım.
    # log_factor 
    log_factor = math.log(ratio_lambda_radius) if ratio_lambda_radius > 0 else 1.0
    
    # 73 Ohm dipol empedansından yola çıkarak kalınlığa göre düzeltme
    # İdeal dipol için L/a ~ 5000: log(5000) ~ 8.5
    # Daha kalın elemanlar için log_factor düşer.
    
    # Basit bir yagi empedans modeli (yaklaşık 50 Ohm hedefi)
    z_base = 50 + 10 * (8.5 - log_factor) / 8.5 # Kalınlık arttıkça Z düşer.
    
    # Eleman uzunlukları ve aralıklara göre ince ayar
    act_ratio = act_len / wavelength
    spacing_ratio = spacing / wavelength
    
    # Aktif eleman uzunluğu rezonanstan sapınca ve aralık değişince empedans değişir.
    z = z_base + 20 * (act_ratio - 0.47) - 10 * (spacing_ratio - 0.18) 
    
    return max(20.0, min(100.0, abs(z))) # Makul aralıkta tut

# SWR tahmini
def estimate_swr(z, target_z=50):
    if abs(z) < target_z:
        return target_z / abs(z)
    else:
        return abs(z) / target_z

# Optimizasyon fonksiyonu (element_cap_m parametresi eklendi)
def optimize_yagi(target_freq_mhz, element_count, step, element_cap_m):
    
    freq_hz = target_freq_mhz * 1e6
    wavelength = C / freq_hz
    
    num_directors = element_count - 2
    if num_directors < 0:
        return None 
        
    best = None
    radius_m = element_cap_m / 2.0 # Çapı yarıçapa çevir
    
    # Eleman uzunlukları için arama faktörleri (step ile belirlenen hassasiyet)
    ref_factors = np.arange(0.50 * 1.03 - 2*step, 0.50 * 1.03 + 2*step + step, step)
    act_factors = np.arange(0.50 - 2*step, 0.50 + 2*step + step, step)
    dir_factors = np.arange(0.46 - 2*step, 0.46 + 2*step + step, step)
    spacing_factors = np.arange(0.18 - 2*step, 0.18 + 2*step + step, step)

    for rf in ref_factors:
        # Kısaltma faktörünü eleman kalınlığına göre burada hesaplayabiliriz
        # Ancak basitlik için sadece empedans tahmininde kullanıyoruz.
        ref_len = rf * wavelength
        for af in act_factors:
            act_len = af * wavelength
            for df in dir_factors:
                dir_len = df * wavelength
                for sf in spacing_factors:
                    spacing = sf * wavelength
                    
                    # Empedans tahmini (radius_m kullanıldı)
                    imp = estimate_impedance(ref_len, act_len, dir_len, spacing, wavelength, radius_m) 
                    swr = estimate_swr(imp)
                    
                    # Kazanç tahmini
                    gain = estimate_gain(element_count, sf) 
                    
                    # SWR ceza puanı
                    swr_penalty = 10 * max(0, swr - 1.5) + (swr - 1.0) * 0.5
                    score = gain - swr_penalty

                    if (best is None) or (score > best["score"]):
                        best = {
                            "reflector": ref_len,
                            "active": act_len,
                            "director": dir_len,
                            "spacing": spacing,
                            "gain": gain,
                            "impedance": imp,
                            "swr": swr,
                            "score": score,
                            "wavelength": wavelength
                        }

    return best

if __name__ == "__main__":
    # Test çağrısı (2m bandı, 4mm çap)
    result = optimize_yagi(target_freq_mhz=145.0, element_count=3, step=0.005, element_cap_m=0.004) 
    print("Optimizasyon Sonucu:\n", result)