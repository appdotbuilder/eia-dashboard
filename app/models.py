from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from decimal import Decimal
from enum import Enum


class DataSourceType(str, Enum):
    STEO = "STEO"  # Short-Term Energy Outlook
    PSM = "PSM"  # Petroleum Supply Monthly
    WEEKLY = "WEEKLY"  # Weekly Petroleum Status Report


class ProductType(str, Enum):
    CRUDE_OIL = "CRUDE_OIL"
    GASOLINE = "GASOLINE"
    DISTILLATE = "DISTILLATE"
    RESIDUAL = "RESIDUAL"
    JET_FUEL = "JET_FUEL"
    PROPANE = "PROPANE"
    NATURAL_GAS = "NATURAL_GAS"


class DispositionType(str, Enum):
    PRODUCTION = "PRODUCTION"
    IMPORTS = "IMPORTS"
    EXPORTS = "EXPORTS"
    STOCK_CHANGE = "STOCK_CHANGE"
    REFINERY_INPUT = "REFINERY_INPUT"
    DEMAND = "DEMAND"


class ScenarioType(str, Enum):
    BASELINE = "BASELINE"
    HURRICANE = "HURRICANE"
    SUPPLY_SHOCK = "SUPPLY_SHOCK"
    DEMAND_SURGE = "DEMAND_SURGE"
    REFINERY_OUTAGE = "REFINERY_OUTAGE"


class SeverityLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    EXTREME = "EXTREME"


# Core Data Models


class EIADataPoint(SQLModel, table=True):
    """Base model for all EIA data points"""

    __tablename__ = "eia_data_points"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    series_id: str = Field(max_length=100, index=True)
    data_source: DataSourceType
    product_type: ProductType
    disposition_type: DispositionType
    period_date: date = Field(index=True)
    value: Decimal = Field(decimal_places=2, max_digits=15)
    unit: str = Field(max_length=50)
    region: Optional[str] = Field(default=None, max_length=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    supply_disposition_entries: List["SupplyDisposition"] = Relationship(back_populates="data_point")


class STEOData(SQLModel, table=True):
    """Short-Term Energy Outlook specific data"""

    __tablename__ = "steo_data"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    series_id: str = Field(max_length=100, index=True)
    product_type: ProductType
    forecast_period: date
    forecast_value: Decimal = Field(decimal_places=2, max_digits=15)
    unit: str = Field(max_length=50)
    confidence_interval_low: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=15)
    confidence_interval_high: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=15)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PSMData(SQLModel, table=True):
    """Petroleum Supply Monthly specific data"""

    __tablename__ = "psm_data"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    series_id: str = Field(max_length=100, index=True)
    product_type: ProductType
    disposition_type: DispositionType
    report_month: date
    value: Decimal = Field(decimal_places=2, max_digits=15)
    unit: str = Field(max_length=50)
    revision_flag: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class WeeklyData(SQLModel, table=True):
    """Weekly Petroleum Status Report data"""

    __tablename__ = "weekly_data"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    series_id: str = Field(max_length=100, index=True)
    product_type: ProductType
    disposition_type: DispositionType
    week_ending: date = Field(index=True)
    value: Decimal = Field(decimal_places=2, max_digits=15)
    unit: str = Field(max_length=50)
    seasonal_adjustment: Optional[str] = Field(default=None, max_length=50)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Supply Disposition Models


class SupplyDisposition(SQLModel, table=True):
    """Supply and disposition balance for petroleum products"""

    __tablename__ = "supply_disposition"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    product_type: ProductType
    period_date: date = Field(index=True)
    data_point_id: Optional[int] = Field(default=None, foreign_key="eia_data_points.id")

    # Supply components
    production: Decimal = Field(default=Decimal("0"), decimal_places=2, max_digits=15)
    imports: Decimal = Field(default=Decimal("0"), decimal_places=2, max_digits=15)
    stock_withdrawal: Decimal = Field(default=Decimal("0"), decimal_places=2, max_digits=15)

    # Disposition components
    exports: Decimal = Field(default=Decimal("0"), decimal_places=2, max_digits=15)
    refinery_input: Decimal = Field(default=Decimal("0"), decimal_places=2, max_digits=15)
    product_supplied: Decimal = Field(default=Decimal("0"), decimal_places=2, max_digits=15)
    stock_build: Decimal = Field(default=Decimal("0"), decimal_places=2, max_digits=15)

    unit: str = Field(max_length=50)
    region: Optional[str] = Field(default=None, max_length=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    data_point: Optional["EIADataPoint"] = Relationship(back_populates="supply_disposition_entries")


# Scenario Planning Models


class Scenario(SQLModel, table=True):
    """Scenario definitions for supply shock simulations"""

    __tablename__ = "scenarios"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=200)
    description: str = Field(max_length=1000)
    scenario_type: ScenarioType
    severity_level: SeverityLevel
    start_date: date
    end_date: date

    # Hurricane specific fields
    hurricane_category: Optional[int] = Field(default=None, ge=1, le=5)
    affected_regions: List[str] = Field(default=[], sa_column=Column(JSON))

    # Supply shock parameters
    production_impact_pct: Decimal = Field(default=Decimal("0"), decimal_places=2, max_digits=5)
    refining_capacity_impact_pct: Decimal = Field(default=Decimal("0"), decimal_places=2, max_digits=5)
    import_disruption_pct: Decimal = Field(default=Decimal("0"), decimal_places=2, max_digits=5)

    # Additional parameters
    parameters: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    is_active: bool = Field(default=True)
    created_by: Optional[str] = Field(default=None, max_length=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    scenario_impacts: List["ScenarioImpact"] = Relationship(back_populates="scenario")
    price_forecasts: List["PriceForecast"] = Relationship(back_populates="scenario")


class ScenarioImpact(SQLModel, table=True):
    """Impact calculations for specific scenarios"""

    __tablename__ = "scenario_impacts"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    scenario_id: int = Field(foreign_key="scenarios.id")
    product_type: ProductType
    disposition_type: DispositionType
    impact_date: date

    baseline_value: Decimal = Field(decimal_places=2, max_digits=15)
    scenario_value: Decimal = Field(decimal_places=2, max_digits=15)
    impact_absolute: Decimal = Field(decimal_places=2, max_digits=15)
    impact_percentage: Decimal = Field(decimal_places=2, max_digits=5)

    unit: str = Field(max_length=50)
    region: Optional[str] = Field(default=None, max_length=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    scenario: "Scenario" = Relationship(back_populates="scenario_impacts")


# Pricing Models


class PriceData(SQLModel, table=True):
    """Historical and current pricing data"""

    __tablename__ = "price_data"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    product_type: ProductType
    price_date: date = Field(index=True)
    price: Decimal = Field(decimal_places=4, max_digits=10)
    price_type: str = Field(max_length=50)  # spot, futures, retail, wholesale
    location: str = Field(max_length=100)
    unit: str = Field(max_length=50)

    # Market indicators
    volume: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=15)
    open_interest: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=15)
    volatility: Optional[Decimal] = Field(default=None, decimal_places=4, max_digits=8)

    created_at: datetime = Field(default_factory=datetime.utcnow)


class PriceForecast(SQLModel, table=True):
    """Price forecasts under different scenarios"""

    __tablename__ = "price_forecasts"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    scenario_id: Optional[int] = Field(default=None, foreign_key="scenarios.id")
    product_type: ProductType
    forecast_date: date
    forecast_price: Decimal = Field(decimal_places=4, max_digits=10)
    baseline_price: Decimal = Field(decimal_places=4, max_digits=10)
    price_impact: Decimal = Field(decimal_places=4, max_digits=10)
    price_impact_pct: Decimal = Field(decimal_places=2, max_digits=5)

    confidence_level: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=5)
    price_type: str = Field(max_length=50)
    location: str = Field(max_length=100)
    unit: str = Field(max_length=50)

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    scenario: Optional["Scenario"] = Relationship(back_populates="price_forecasts")


# Seasonality Models


class SeasonalPattern(SQLModel, table=True):
    """Seasonal patterns for different products and regions"""

    __tablename__ = "seasonal_patterns"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    product_type: ProductType
    disposition_type: DispositionType
    month: int = Field(ge=1, le=12)
    region: Optional[str] = Field(default=None, max_length=100)

    # Seasonal adjustment factors
    seasonal_index: Decimal = Field(decimal_places=4, max_digits=6)
    trend_factor: Decimal = Field(default=Decimal("1.0"), decimal_places=4, max_digits=6)
    volatility_multiplier: Decimal = Field(default=Decimal("1.0"), decimal_places=4, max_digits=6)

    # Historical basis
    years_of_data: int = Field(default=10, ge=1)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class HurricaneHistorical(SQLModel, table=True):
    """Historical hurricane impact data for model calibration"""

    __tablename__ = "hurricane_historical"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    hurricane_name: str = Field(max_length=100)
    year: int = Field(ge=1950)
    category: int = Field(ge=1, le=5)
    landfall_date: date

    affected_regions: List[str] = Field(default=[], sa_column=Column(JSON))

    # Impact metrics
    refinery_capacity_lost_pct: Decimal = Field(default=Decimal("0"), decimal_places=2, max_digits=5)
    production_disruption_days: int = Field(default=0, ge=0)
    price_spike_gasoline_pct: Decimal = Field(default=Decimal("0"), decimal_places=2, max_digits=8)
    price_spike_crude_pct: Decimal = Field(default=Decimal("0"), decimal_places=2, max_digits=8)

    # Recovery metrics
    recovery_days_production: int = Field(default=0, ge=0)
    recovery_days_refining: int = Field(default=0, ge=0)

    notes: Optional[str] = Field(default=None, max_length=1000)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Dashboard Configuration Models


class DashboardConfig(SQLModel, table=True):
    """Configuration for dashboard displays and reports"""

    __tablename__ = "dashboard_config"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    config_name: str = Field(max_length=100, unique=True)
    dashboard_type: str = Field(max_length=50)  # supply_disposition, scenario_analysis, price_forecast

    # Display configuration
    chart_configs: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    data_filters: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    refresh_interval_minutes: int = Field(default=60, ge=1)

    # Report settings
    default_date_range_days: int = Field(default=365, ge=1)
    include_forecasts: bool = Field(default=True)
    include_scenarios: bool = Field(default=False)

    is_active: bool = Field(default=True)
    created_by: Optional[str] = Field(default=None, max_length=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ReportTemplate(SQLModel, table=True):
    """Templates for automated reports"""

    __tablename__ = "report_templates"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    template_name: str = Field(max_length=200)
    report_type: str = Field(max_length=50)  # weekly_summary, scenario_analysis, price_alert

    # Template configuration
    data_sources: List[str] = Field(default=[], sa_column=Column(JSON))
    products_included: List[str] = Field(default=[], sa_column=Column(JSON))
    regions_included: List[str] = Field(default=[], sa_column=Column(JSON))

    # Output format
    output_format: str = Field(max_length=20, default="PDF")  # PDF, CSV, JSON
    chart_specifications: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))

    # Scheduling
    schedule_pattern: Optional[str] = Field(default=None, max_length=100)  # cron-like pattern
    auto_send: bool = Field(default=False)
    recipients: List[str] = Field(default=[], sa_column=Column(JSON))

    is_active: bool = Field(default=True)
    created_by: Optional[str] = Field(default=None, max_length=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Alert and Monitoring Models


class DataAlert(SQLModel, table=True):
    """Alerts for data anomalies and significant changes"""

    __tablename__ = "data_alerts"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    alert_name: str = Field(max_length=200)
    alert_type: str = Field(max_length=50)  # threshold, anomaly, missing_data, price_spike

    # Alert criteria
    product_type: Optional[ProductType] = Field(default=None)
    threshold_value: Optional[Decimal] = Field(default=None, decimal_places=4, max_digits=15)
    threshold_operator: Optional[str] = Field(default=None, max_length=10)  # >, <, >=, <=, =

    # Configuration
    check_frequency_minutes: int = Field(default=60, ge=1)
    cooldown_hours: int = Field(default=24, ge=1)
    severity_level: SeverityLevel = Field(default=SeverityLevel.MODERATE)

    is_active: bool = Field(default=True)
    last_triggered: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Non-persistent schemas for API and validation


class EIADataPointCreate(SQLModel, table=False):
    series_id: str = Field(max_length=100)
    data_source: DataSourceType
    product_type: ProductType
    disposition_type: DispositionType
    period_date: date
    value: Decimal = Field(decimal_places=2, max_digits=15)
    unit: str = Field(max_length=50)
    region: Optional[str] = Field(default=None, max_length=100)


class ScenarioCreate(SQLModel, table=False):
    name: str = Field(max_length=200)
    description: str = Field(max_length=1000)
    scenario_type: ScenarioType
    severity_level: SeverityLevel
    start_date: date
    end_date: date
    hurricane_category: Optional[int] = Field(default=None, ge=1, le=5)
    affected_regions: List[str] = Field(default=[])
    production_impact_pct: Decimal = Field(default=Decimal("0"), decimal_places=2, max_digits=5)
    refining_capacity_impact_pct: Decimal = Field(default=Decimal("0"), decimal_places=2, max_digits=5)
    import_disruption_pct: Decimal = Field(default=Decimal("0"), decimal_places=2, max_digits=5)
    parameters: Dict[str, Any] = Field(default={})


class ScenarioUpdate(SQLModel, table=False):
    name: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    severity_level: Optional[SeverityLevel] = Field(default=None)
    start_date: Optional[date] = Field(default=None)
    end_date: Optional[date] = Field(default=None)
    production_impact_pct: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=5)
    refining_capacity_impact_pct: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=5)
    import_disruption_pct: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=5)
    parameters: Optional[Dict[str, Any]] = Field(default=None)
    is_active: Optional[bool] = Field(default=None)


class DashboardConfigCreate(SQLModel, table=False):
    config_name: str = Field(max_length=100)
    dashboard_type: str = Field(max_length=50)
    chart_configs: Dict[str, Any] = Field(default={})
    data_filters: Dict[str, Any] = Field(default={})
    refresh_interval_minutes: int = Field(default=60, ge=1)
    default_date_range_days: int = Field(default=365, ge=1)
    include_forecasts: bool = Field(default=True)
    include_scenarios: bool = Field(default=False)


class SupplyDispositionSummary(SQLModel, table=False):
    """Summary view for supply disposition data"""

    product_type: ProductType
    period_date: date
    total_supply: Decimal = Field(decimal_places=2, max_digits=15)
    total_disposition: Decimal = Field(decimal_places=2, max_digits=15)
    balance: Decimal = Field(decimal_places=2, max_digits=15)
    unit: str
    region: Optional[str] = Field(default=None)
