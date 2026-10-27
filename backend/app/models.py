from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sku = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    base_price = Column(Float, nullable=False)
    cogs = Column(Float, nullable=True)  # Cost of Goods Sold per unit
    inventory_count = Column(Integer, default=0, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    transactions = relationship("SalesTransaction", back_populates="product", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Product(sku='{self.sku}', name='{self.name}', category='{self.category}')>"


class SalesTransaction(Base):
    __tablename__ = "sales_transactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    transaction_code = Column(String(100), unique=True, index=True, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    sale_date = Column(Date, nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)  # Original catalog/list price
    discount_pct = Column(Float, default=0.0, nullable=False)  # Discount percentage (e.g. 10.0 for 10%)
    actual_selling_price = Column(Float, nullable=False)  # Price after discount
    cogs_per_unit = Column(Float, nullable=True)  # Unit cost at time of transaction
    revenue = Column(Float, nullable=False)  # quantity * actual_selling_price
    gross_profit = Column(Float, nullable=True)  # revenue - (quantity * cogs_per_unit)
    gross_margin = Column(Float, nullable=True)  # gross_profit / revenue
    channel = Column(String(50), default="Direct", nullable=False)
    is_synthetic = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    product = relationship("Product", back_populates="transactions")

    __table_args__ = (
        Index("idx_txn_prod_date", "product_id", "sale_date"),
        Index("idx_txn_date_revenue", "sale_date", "revenue"),
    )

    def __repr__(self):
        return f"<SalesTransaction(code='{self.transaction_code}', product_id={self.product_id}, revenue={self.revenue})>"


class ImportLog(Base):
    __tablename__ = "import_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    row_count = Column(Integer, default=0, nullable=False)
    valid_count = Column(Integer, default=0, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)
    status = Column(String(50), nullable=False)  # 'SUCCESS', 'ROLLED_BACK', 'FAILED'
    details = Column(Text, nullable=True)  # JSON or markdown formatted error messages/summary
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<ImportLog(filename='{self.filename}', status='{self.status}', valid={self.valid_count})>"
