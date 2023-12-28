from sqlalchemy import and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound

from personaltwilog.db.base import Base
from personaltwilog.db.model import ExternalLink


class ExternalLinkDB(Base):
    def __init__(self, db_path: str = "timeline.db"):
        super().__init__(db_path)

    def select(self):
        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()
        result = session.query(ExternalLink).all()
        session.close()
        return result

    def upsert(self, record: ExternalLink | list[dict]) -> list[int]:
        """upsert

        Args:
            record (ExternalLink | list[dict]): 投入レコード、またはレコード辞書のリスト

        Returns:
            list[int]: レコードに対応した投入結果のリスト
                       追加したレコードは0、更新したレコードは1が入る
        """
        result: list[int] = []
        record_list: list[ExternalLink] = []
        if isinstance(record, ExternalLink):
            record_list = [record]
        elif isinstance(record, list):
            if len(record) == 0:
                return []
            if not isinstance(record[0], dict):
                return []
            record_list = [ExternalLink.create(r) for r in record]

        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()

        for r in record_list:
            try:
                q = (
                    session.query(ExternalLink)
                    .filter(and_(ExternalLink.tweet_id == r.tweet_id, ExternalLink.registered_at == r.registered_at))
                    .with_for_update()
                )
                p = q.one()
            except NoResultFound:
                # INSERT
                session.add(r)
                result.append(0)
            else:
                # UPDATE
                # idと日付関係以外を更新する
                p.tweet_id = r.tweet_id
                p.tweet_url = r.tweet_url
                p.external_link_url = r.external_link_url
                p.external_link_type = r.external_link_type
                # p.created_at = r.created_at
                # p.appeared_at = r.appeared_at
                # p.registered_at = r.registered_at
                result.append(1)

        session.commit()
        session.close()
        return result