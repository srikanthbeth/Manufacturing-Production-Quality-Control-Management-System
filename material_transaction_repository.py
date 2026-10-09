from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.material_transaction import MaterialTransaction


class MaterialTransactionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        transaction: MaterialTransaction,
    ) -> MaterialTransaction:
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)

        return transaction

    def get_history(
        self,
        material_id: int,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[MaterialTransaction], int]:

        base_statement = select(
            MaterialTransaction
        ).where(
            MaterialTransaction.material_id
            == material_id
        )

        count_statement = select(
            func.count()
        ).select_from(
            base_statement.subquery()
        )

        total = self.db.execute(
            count_statement
        ).scalar_one()

        offset = (page - 1) * page_size

        statement = (
            base_statement
            .order_by(
                MaterialTransaction.id.desc()
            )
            .offset(offset)
            .limit(page_size)
        )

        transactions = list(
            self.db.execute(
                statement
            ).scalars().all()
        )

        return transactions, total