# Advanced Crypto Trading Predictor

Backend FastAPI yang menarik data candle real-time Binance, menghitung indikator SMA20/50, RSI, dan ATR, lalu mengembalikan rekomendasi BUY/SELL lengkap dengan Entry, TP, SL, dan confidence score.

## Prasyarat
- Python 3.10+
- Koneksi internet (untuk memanggil API publik Binance)
- Browser/klien frontend dapat memanggil API langsung karena CORS diizinkan untuk semua origin
- API akan menolak request jika data candle yang dikembalikan Binance kurang dari 60 bar
  (dibutuhkan untuk indikator SMA/RSI/ATR)

## Instalasi
```bash
pip install -r requirements.txt
```

## Menjalankan server
```bash
uvicorn server:app --reload --port 8000
```

Endpoint root tersedia di `GET /`.

## Menggunakan endpoint /predict
Contoh permintaan:
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTCUSDT", "timeframe": "1h"}'
```

Timeframe yang didukung: `1m`, `5m`, `15m`, `1h`, `4h`, `1d`.

## Response contoh
```json
{
  "symbol": "BTCUSDT",
  "timeframe": "1h",
  "timestamp": "2024-06-01T12:34:56.000Z",
  "signal": "BUY",
  "entry": 27123.45,
  "take_profit": 27789.12,
  "stop_loss": 26791.23,
  "confidence": 0.31,
  "short_sma": 27010.12,
  "long_sma": 26895.44,
  "rsi": 55.21,
  "atr": 184.32
}
```

## Integrasi frontend cepat
Cuplikan JavaScript siap pakai (contoh di `index.html`):
```js
const response = await fetch('http://localhost:8000/predict', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ symbol: 'BTCUSDT', timeframe: '1h' })
});
const data = await response.json();
console.log(data);
```

## Catatan
- Gunakan simbol pasangan Binance, mis. `BTCUSDT`, `ETHUSDT`.
- Pastikan rate limit Binance dipatuhi jika di-deploy di produksi.
- Penentuan TP/SL berbasis ATR dengan multiplier 1.8 untuk TP dan 1.0 untuk SL.
