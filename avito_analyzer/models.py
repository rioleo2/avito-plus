from typing import List, Optional
from pydantic import BaseModel, Field


class FilterParams(BaseModel):
    query: str = Field(..., description="Поисковый запрос, например 'MacBook Pro M1'")
    city: str = Field("Москва", description="Город в свободной форме: «Казань», «Нижний Новгород», «kazan»")
    radius: Optional[int] = Field(None, description="Радиус поиска в км")
    price_from: Optional[int] = Field(None, description="Минимальная цена")
    price_to: Optional[int] = Field(None, description="Максимальная цена")
    only_market_prices: bool = Field(False, description="Только рыночные цены")
    seller_type: str = Field("all", description="Тип продавца: all, private, company")
    min_rating: bool = Field(False, description="Рейтинг от 4.7")
    contact_type: str = Field("all", description="Способы связи: all, calls, messages")

    # Дополнительные фильтры
    delivery: bool = Field(False, description="С Авито Доставкой")
    pickup: bool = Field(False, description="С Авито Самовывозом")
    has_return: bool = Field(False, description="Есть возврат")
    installments: bool = Field(False, description="Оплата частями")
    warranty: bool = Field(False, description="Авито Гарантия")
    markdown: bool = Field(False, description="Уценка")

    # Текстовые фильтры
    words_in_description: Optional[str] = Field(None, description="Слова в описании")
    exclude_words: Optional[str] = Field(None, description="Скрыть объявления со словами")

    # Сколько страниц выдачи Авито собрать (на странице ~50 объявлений)
    pages: int = Field(3, ge=1, le=5, description="Страниц выдачи Авито")
    use_cache: bool = Field(True, description="Брать выдачу из кэша, если она свежая (до 20 минут)")
    # Сколько лучших кандидатов открыть и сверить цену/описание на странице объявления
    verify_top: int = Field(12, ge=0, le=30, description="Сколько лучших объявлений проверять на странице")


class AIAnalysis(BaseModel):
    summary: str = Field("", description="Краткое резюме лота")
    why_good: List[str] = Field(default_factory=list, description="Почему это объявление выгодно")
    risks_and_defects: List[str] = Field(default_factory=list, description="Возможные риски, дефекты или нюансы")
    extracted_specs: dict = Field(default_factory=dict, description="Извлеченные характеристики")
    deal_rating: int = Field(5, description="Оценка выгодности сделки от 1 до 10")
    estimated_profit: Optional[int] = Field(None, description="Выгода в рублях относительно медианы рынка")
    verdict: str = Field("Нейтрально", description="Вердикт по сделке")
    source: str = Field("heuristic", description="Кто оценивал: 'llm' или 'heuristic'")
    is_target: bool = Field(True, description="Это именно искомый товар, а не аксессуар/запчасти/услуга")
    critical: bool = Field(False, description="Критичный риск: блокировка, неисправность, запчасти, признаки обмана")
    condition_score: Optional[int] = Field(None, description="Оценка состояния/качества объявления 1-10 (только от ИИ)")


class ListingItem(BaseModel):
    id: str
    title: str
    price: int
    url: str
    location: str = ""
    date_posted: str = ""
    seller: str = ""
    badge: str = ""  # ярлык самого Авито, например «Рыночная цена»
    image_url: Optional[str] = None
    images: List[str] = Field(default_factory=list)
    description_snippet: str = ""
    full_description: str = ""

    # Проверка на странице объявления
    price_verified: Optional[bool] = Field(None, description="None — не проверялось, True — цена совпала, False — цена изменилась")
    listed_price: Optional[int] = Field(None, description="Цена из выдачи, если на странице она оказалась другой")
    unavailable: bool = Field(False, description="Объявление снято с публикации")
    suspicious: bool = Field(False, description="Цена подозрительно низкая относительно рынка")
    price_note: str = ""

    # Рыночная оценка
    relevant: bool = Field(True, description="Похоже ли на искомый товар (не аксессуар/запчасти)")
    discount_pct: Optional[float] = Field(None, description="Скидка к медиане рынка, %")
    score: float = Field(0.0, description="Итоговый балл выгодности для сортировки")
    ai_analysis: Optional[AIAnalysis] = None


class MarketStats(BaseModel):
    total_listings: int
    min_price: int
    max_price: int
    avg_price: int
    median_price: int
    p25_price: int  # Выгодная граница (нижний квартиль)
    p75_price: int  # Верхняя рыночная граница
    price_distribution: List[dict] = Field(default_factory=list)


class AnalysisResponse(BaseModel):
    query: str
    city: str
    stats: MarketStats
    listings: List[ListingItem]
    best_deals: List[str] = Field(default_factory=list, description="id лучших предложений по порядку")
    pages_scraped: int = 0
    scraped_total: int = 0
    verified_count: int = 0
    llm_used: bool = False
    warnings: List[str] = Field(default_factory=list)


class JobStatus(BaseModel):
    job_id: str
    state: str = "running"  # running | done | error | cancelled
    stage: str = ""
    progress: int = 0  # 0..100
    error: Optional[str] = None
    result: Optional[AnalysisResponse] = None
