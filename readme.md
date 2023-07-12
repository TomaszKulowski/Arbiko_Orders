# General info
'Arbiko Orders' is an app for easy browsing orders from the arbiko.pl shop.

## Technologies 
Python 3.11

### Setup

1. Clone repo

    ```bash
    git clone https://github.com/Tomasz987/arbiko_orders.git
    ```
    
2. Install requirements packages

    ```bash
    pip install -r requirements.txt
    ```

### Usage

```bash
usage: main.py [-h] [-r | -u | -s] [-start_date START_DATE] [-end_date END_DATE]

options:
  -h, --help              show this help message and exit
  -r, --refresh           refresh the database
  -u, --update            update the database
  -s, --search            choose to search data
  -start_date START_DATE  date format: YYYY-MM-DD
  -end_date END_DATE      date format: YYYY-MM-DD
```
