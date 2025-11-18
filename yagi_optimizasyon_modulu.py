# yagi_optimizasyon_modulu.py
"""
Basit Yagi Optimizasyon Modülü
Bu modül, temel Yagi-Uda tasarımı için grid search tabanlı optimizasyon yapar.
Parametreler: Reflektör uzunluğu, aktif eleman uzunluğu, direktör uzunluğu,
eleman aralıkları.
"""
import numpy as np
import math

# Işık hızı (m/s)
C = 299792458.0

# Temel kazanç tahmini (empirik, kaba bir model)
def estimate_gain(num_elements, spacing_factor):
    # Spacing factor lambdanın çarpanı (örneğin 0.18)
    base_gain = 2.15 # Dipol kazancı
    # Eleman sayısına göre temel kazanç artışı
    gain_increase = 0.8 * (num_elements - 1)
    # Aralık faktörüne göre ayar (çok dar veya çok geniş aralık ceza getirir)
    spacing_penalty = 10 * (spacing_factor - 0.18)**2 
    gain = base_gain + gain_increase - spacing_penalty
    return max(3.0, gain) # Minimum bir değer tut

# Empedans tahmini (50 Ohm'a yakınlaştıran kaba bir model)
def estimate_impedance(ref_len, act_len, dir_len, spacing, wavelength):
    # Tüm uzunluklar metre cinsinden
    # Eleman uzunlukları lambda'ya göre ayarlanır
    act_ratio = act_len / wavelength
    ref_ratio = ref_len / wavelength
    dir_ratio = dir_len / wavelength
    spacing_ratio = spacing / wavelength
    
    # Empirik formül (yaklaşık)
    z = 50 + 20 * (act_ratio - 0.47) - 10 * (spacing_ratio - 0.18)
    
    return max(20.0, min(100.0, abs(z))) # Makul aralıkta tut

# SWR tahmini
def estimate_swr(z, target_z=50):
    if abs(z) < target_z:
        return target_z / abs(z)
    else:
        return abs(z) / target_z

# Optimizasyon fonksiyonu
def optimize_yagi(target_freq_mhz, element_count, step):
    
    freq_hz = target_freq_mhz * 1e6
    wavelength = C / freq_hz
    
    # Eleman sayısını (Reflektör + Aktif + Direktörler) kullanarak direktör sayısını bul
    num_directors = element_count - 2
    
    if num_directors < 0:
        return None # Yagi en az 2 elemanlı olmalı
        
    best = None
    
    # Optimizasyon aralıkları (lambda'nın çarpanları)
    # Varsayılan değerler etrafında daha hassas arama
    ref_factors = np.arange(0.50 * 1.03 - 2*step, 0.50 * 1.03 + 2*step + step, step)
    act_factors = np.arange(0.50 - 2*step, 0.50 + 2*step + step, step)
    dir_factors = np.arange(0.46 - 2*step, 0.46 + 2*step + step, step)
    spacing_factors = np.arange(0.18 - 2*step, 0.18 + 2*step + step, step)

    for rf in ref_factors:
        ref_len = rf * wavelength
        for af in act_factors:
            act_len = af * wavelength
            for df in dir_factors:
                dir_len = df * wavelength
                for sf in spacing_factors:
                    spacing = sf * wavelength
                    
                    # Empedans ve SWR tahmini (kaba model)
                    imp = estimate_impedance(ref_len, act_len, dir_len, spacing, wavelength)
                    swr = estimate_swr(imp)
                    
                    # Kazanç tahmini
                    gain = estimate_gain(element_count, sf) # sf = spacing_factor
                    
                    # Amaç: Kazancı maksimize etmek ve SWR'yi minimize etmek
                    # SWR = 1.0 için ceza 0; SWR > 1.5 için büyük ceza
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
    # Test çağrısı (2m bandı)
    result = optimize_yagi(145.0, element_count=3, step=0.005)
    print("Optimizasyon Sonucu:\n", result)