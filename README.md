# DataInsight

A Streamlit web app that lets you upload a CSV or Excel file and instantly get a full data profile, cleaning tools, filters, and a set of suggested analyses. No code required.

I built this after getting tired of writing the same ten lines of pandas every time I opened a new dataset: check the shape, check for nulls, groupby a category, plot a trend. DataInsight automates that first pass so you can jump straight to the questions that actually matter.

## What it does

**Upload & read**
- Accepts CSV, XLS, and XLSX
- CSV reading tries multiple encodings (UTF-8, ISO-8859-1, cp1252) and falls back to auto-detecting the delimiter, so files exported from different tools don't break the upload

**Data quality tools**
- Missing value handling per column: drop rows, fill with mean/median/mode, or a custom value
- Duplicate row detection and removal
- Manual column type override, for cases where auto-detection gets it wrong (a ZIP code read as a number, for example)

**Interactive filters**
- Date range picker for detected datetime columns
- Multi-select filters for categorical columns
- A search box to find specific rows in the preview table

**Suggested analyses** (auto-generated based on what's in your dataset)
- Sales/profit trend over time
- Month-over-month growth rate
- Sales/profit breakdown by category
- Top & bottom performers for a chosen metric and dimension
- Correlation heatmap between numeric columns
- Outlier detection using the IQR method

**Export**
- Every analysis result can be downloaded as CSV, Excel, or a PNG chart

**Theme**
- Dark/light mode toggle

## Tech stack

- Python
- Streamlit
- pandas / numpy
- matplotlib (for exportable chart images)
- openpyxl / xlrd (Excel read/write)

## Running it locally

```bash
git clone https://github.com/Nbill27/datainsight.git
cd datainsight
pip install -r requirements.txt
streamlit run app.py
```

The app opens at `http://localhost:8501`.

## Project structure

```
datainsight/
├── app.py              # main application
├── requirements.txt
└── README.md
```

## Author

Nabil Deja 
[GitHub](https://github.com/Nbill27)
