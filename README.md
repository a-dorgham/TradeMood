# TradeMood

![Python](https://img.shields.io/badge/Python-3.10-blue.svg)
![Streamlit](https://img.shields.io/badge/GUI-Streamlit-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![TensorFlow](https://img.shields.io/badge/Deep%20Learning-TensorFlow-orange?logo=tensorflow)
![Plotly](https://img.shields.io/badge/Visualization-Plotly-darkorange?logo=plotly)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)
![Contributions](https://img.shields.io/badge/Contributions-Welcome-ff69b4)

**TradeMood** is a Python-based, web-accessible dashboard for real-time financial market sentiment analysis and trading decision support. Built with **Streamlit**, it integrates sentiment analysis using a pre-trained RoBERTa model (`finiteautomata/bertweet-base-sentiment-analysis`), fetches market data and social media content, generates trading signals, and tracks trades for financial instruments like gold futures (`GC=F`). **Still requires fine tuning.**

---

## 🔧 Features

- 🖥️ **Interactive Web Dashboard** powered by **Streamlit**.
- 📊 **Real-Time Sentiment Analysis** using a RoBERTa-based model.
- 📈 **Trading Signal Generation** based on sentiment trends (BUY, SELL, HOLD).
- 💰 **Trade Management** with position tracking and P&L calculation.
- 📅 **Scheduled Sentiment Pipeline** every 5 minutes during COMEX hours.
- 🗄️ **SQLite Database** for caching and trade history.
- 🔍 **Detailed Trade History** with styled P&L metrics.
- ⚠️ **Robust Error Handling** and logging.
- 🔄 **Modular Architecture** for easy extension.
- 📉 **Market Data Integration** (e.g., Yahoo Finance `GC=F`).
- 🧪 **Unit Tests** for key components.

---

## 📁 Project Structure

```
TradeMood/
├── README.md
├── requirements.txt
├── LICENSE
├── trademood/
│   ├── core/
│   │   ├── database_handler.py
│   │   ├── error_handler.py
│   │   ├── trade_tracker.py
│   │   ├── models/
│   │   │   ├── sentiment_result.py
│   │   │   ├── trading_signal.py
│   │   │   └── trend_signal.py
│   │   ├── sentiment/
│   │   │   ├── analyzer.py
│   │   │   ├── fetcher.py
│   │   │   ├── pipeline.py
│   │   │   ├── trend_generator.py
│   │   │   └── signal_generator.py
│   ├── api/
│   │   └── sentiment_api.py
│   ├── dashboard/
│   │   └── app.py
│   └── tests/
│       └── test_sentiment.py
├── scripts/
│   └── run_dashboard.py
├── data/
│   └── sentiment_cache.db
├── examples/
│   └── config.yaml
└── docs/
    └── screenshots/
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10.5
- Virtual environment (recommended)
- SQLite database
- API keys (Yahoo Finance, X API, etc.)

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run the App

```bash
streamlit run scripts/run_dashboard.py
```

Access the dashboard at: `http://localhost:8501`

---

## 📚 Usage

1. **View Sentiment Trends** for `GC=F`
2. **Check Trading Signals** (BUY, SELL, HOLD)
3. **Manage Trades**: Open/close positions, track P&L
4. **Review History** in styled trade table
5. **Edit `config.yaml`** for API and symbols

---

## 🧩 Supported Instruments

- ✅ Gold Futures (`GC=F`)
- 🚧 Add more via `fetcher.py` and `trade_tracker.py`

---


## 🛠 Developer Notes

- Add new instruments in `fetcher.py`, `trade_tracker.py`
- Change model in `analyzer.py`
- Extend API in `sentiment_api.py`

---

## 🧪 Testing

```bash
pytest trademood/tests/
```

---

## 📸 Screenshots

<img width="1598" alt="Full Upper Dashboard" src="https://github.com/user-attachments/assets/50697ee6-4f92-4f59-8599-2e0d77d58731" />

---
<img width="1032" alt="Price Action with Sentiment" src="https://github.com/user-attachments/assets/d0f4548d-0902-4ebc-8fb5-28194c481e4e" />

---

<img width="1216" alt="Trade History" src="https://github.com/user-attachments/assets/598e49f4-31b7-4b3b-80e4-01409d9e5699" />

---

<img width="1171" alt="Database Tables" src="https://github.com/user-attachments/assets/faa10344-25cb-4e36-8e76-44d5f2ef5f5e" />


---

## 🌐 Roadmap

- 📈 More instruments (stocks, forex, crypto)
- 🧠 Multi-language sentiment models
- 💼 Live broker integration
- ⚙️ Config UI

---

## 🤝 Contributing

```bash
git clone https://github.com/your-username/TradeMood.git
cd TradeMood
```

---

## 📜 License

MIT License — see `LICENSE`.

---

## 📬 Contact

- Email: [a.k.y.dorgham@gmail.com](mailto:a.k.y.dorgham@gmail.com)
- GitHub Issues: [TradeMood Issues](https://github.com/a-dorgham/TradeMood/issues)
- Connect: [LinkedIn](https://www.linkedin.com/in/abdeldorgham) | [GoogleScholar](https://scholar.google.com/citations?user=EOwjslcAAAAJ&hl=en)  | [ResearchGate](https://www.researchgate.net/profile/Abdel-Dorgham-2) | [ORCiD](https://orcid.org/0000-0001-9119-5111)

---

## ⚠️ Limitations

- No automated order execution
- Limited offline functionality
- SQLite not suited for large data
- Sentiment model limitations
