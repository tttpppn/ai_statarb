# AI Stock Universe: 30+ AI-focused US stocks
# Mix of sectors: Semiconductors, Software, Cloud, Semiconductors Equipment, Chip Design
# Used for pairs trading, mean reversion detection

AI_STOCKS_UNIVERSE = [
    # ===== SEMICONDUCTORS / CHIP DESIGN (11 stocks) =====
    {"ticker": "NVDA", "name": "NVIDIA", "sector": "semiconductors", "subsector": "GPU/AI", "market_cap": "3T"},
    {"ticker": "AMD", "name": "Advanced Micro Devices", "sector": "semiconductors", "subsector": "CPU/GPU", "market_cap": "200B"},
    {"ticker": "QCOM", "name": "Qualcomm", "sector": "semiconductors", "subsector": "Mobile", "market_cap": "160B"},
    {"ticker": "INTC", "name": "Intel", "sector": "semiconductors", "subsector": "CPU", "market_cap": "90B"},
    {"ticker": "MRVL", "name": "Marvell Technology", "sector": "semiconductors", "subsector": "Data Center", "market_cap": "55B"},
    {"ticker": "AVGO", "name": "Broadcom", "sector": "semiconductors", "subsector": "Infrastructure", "market_cap": "230B"},
    {"ticker": "ASML", "name": "ASML Holdings", "sector": "semiconductors", "subsector": "Equipment", "market_cap": "270B"},
    {"ticker": "LRCX", "name": "Lam Research", "sector": "semiconductors", "subsector": "Equipment", "market_cap": "78B"},
    {"ticker": "NXPI", "name": "NXP Semiconductors", "sector": "semiconductors", "subsector": "Automotive/IoT", "market_cap": "65B"},
    {"ticker": "MU", "name": "Micron Technology", "sector": "semiconductors", "subsector": "Memory", "market_cap": "100B"},
    {"ticker": "TSM", "name": "Taiwan Semiconductor", "sector": "semiconductors", "subsector": "Foundry", "market_cap": "580B"},

    # ===== SOFTWARE / GENERATIVE AI (8 stocks) =====
    {"ticker": "MSFT", "name": "Microsoft", "sector": "software", "subsector": "Cloud/AI", "market_cap": "3.1T"},
    {"ticker": "GOOGL", "name": "Alphabet", "sector": "software", "subsector": "Search/AI", "market_cap": "2.1T"},
    {"ticker": "META", "name": "Meta", "sector": "software", "subsector": "Social/AI", "market_cap": "600B"},
    {"ticker": "CRM", "name": "Salesforce", "sector": "software", "subsector": "Enterprise/AI", "market_cap": "280B"},
    {"ticker": "ADBE", "name": "Adobe", "sector": "software", "subsector": "Creative/AI", "market_cap": "210B"},
    {"ticker": "SNPS", "name": "Synopsys", "sector": "software", "subsector": "Chip Design Tools", "market_cap": "75B"},
    {"ticker": "CDNS", "name": "Cadence", "sector": "software", "subsector": "Chip Design Tools", "market_cap": "80B"},
    {"ticker": "NFLX", "name": "Netflix", "sector": "software", "subsector": "Streaming/Recommendation", "market_cap": "280B"},

    # ===== CLOUD / INFRASTRUCTURE (6 stocks) =====
    {"ticker": "AMZN", "name": "Amazon", "sector": "cloud", "subsector": "Cloud/Retail", "market_cap": "2.2T"},
    {"ticker": "CRWD", "name": "CrowdStrike", "sector": "cloud", "subsector": "Security", "market_cap": "85B"},
    {"ticker": "NET", "name": "Cloudflare", "sector": "cloud", "subsector": "Edge Computing", "market_cap": "40B"},
    {"ticker": "DDOG", "name": "Datadog", "sector": "cloud", "subsector": "Monitoring/AI", "market_cap": "50B"},
    {"ticker": "SNOW", "name": "Snowflake", "sector": "cloud", "subsector": "Data Platform", "market_cap": "40B"},
    {"ticker": "WDAY", "name": "Workday", "sector": "cloud", "subsector": "HCM", "market_cap": "60B"},

    # ===== SEMICONDUCTORS EQUIPMENT (3 stocks) =====
    {"ticker": "AMAT", "name": "Applied Materials", "sector": "semiconductors_equipment", "subsector": "Fab Equipment", "market_cap": "150B"},
    {"ticker": "KLAC", "name": "KLA", "sector": "semiconductors_equipment", "subsector": "Inspection Equipment", "market_cap": "55B"},
    {"ticker": "ONTO", "name": "Onto Innovation", "sector": "semiconductors_equipment", "subsector": "Process Equipment", "market_cap": "25B"},

    # ===== AI INFRASTRUCTURE & SERVICES (4 stocks) =====
    {"ticker": "PLTR", "name": "Palantir", "sector": "ai_infrastructure", "subsector": "Data Analytics", "market_cap": "120B"},
    {"ticker": "ARM", "name": "Arm Holdings", "sector": "ai_infrastructure", "subsector": "Chip Architecture", "market_cap": "50B"},
    {"ticker": "SMCI", "name": "Super Micro Computer", "sector": "ai_infrastructure", "subsector": "AI Servers", "market_cap": "60B"},
    {"ticker": "DELL", "name": "Dell Technologies", "sector": "ai_infrastructure", "subsector": "Servers/Storage", "market_cap": "75B"},
]

# Quick lookup by ticker
TICKER_MAP = {stock["ticker"]: stock for stock in AI_STOCKS_UNIVERSE}

# Group by sector for correlation analysis
STOCKS_BY_SECTOR = {}
for stock in AI_STOCKS_UNIVERSE:
    sector = stock["sector"]
    if sector not in STOCKS_BY_SECTOR:
        STOCKS_BY_SECTOR[sector] = []
    STOCKS_BY_SECTOR[sector].append(stock)

def get_stock(ticker):
    """Get stock info by ticker."""
    return TICKER_MAP.get(ticker)

def get_stocks_in_sector(sector):
    """Get all stocks in a sector."""
    return STOCKS_BY_SECTOR.get(sector, [])

def get_all_tickers():
    """Get all tickers in universe."""
    return [stock["ticker"] for stock in AI_STOCKS_UNIVERSE]
