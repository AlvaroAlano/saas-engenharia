import unicodedata
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/simulador", tags=["Simulador"])

# Mapeamento do Custo Unitário Básico (CUB) de referência por UF (em R$/m²)
CUB_REFERENCIA = {
    "AC": {"alto": 2400.0, "medio": 1850.0, "baixo": 1500.0},
    "AL": {"alto": 2450.0, "medio": 1900.0, "baixo": 1520.0},
    "AP": {"alto": 2350.0, "medio": 1800.0, "baixo": 1480.0},
    "AM": {"alto": 2550.0, "medio": 1950.0, "baixo": 1580.0},
    "BA": {"alto": 2500.0, "medio": 1950.0, "baixo": 1550.0},
    "CE": {"alto": 2500.0, "medio": 1950.0, "baixo": 1550.0},
    "DF": {"alto": 2950.0, "medio": 2350.0, "baixo": 1950.0},
    "ES": {"alto": 2600.0, "medio": 2000.0, "baixo": 1620.0},
    "GO": {"alto": 2600.0, "medio": 2000.0, "baixo": 1600.0},
    "MA": {"alto": 2380.0, "medio": 1850.0, "baixo": 1490.0},
    "MT": {"alto": 2580.0, "medio": 2000.0, "baixo": 1620.0},
    "MS": {"alto": 2550.0, "medio": 1980.0, "baixo": 1600.0},
    "MG": {"alto": 2650.0, "medio": 2050.0, "baixo": 1650.0},
    "PA": {"alto": 2400.0, "medio": 1880.0, "baixo": 1510.0},
    "PB": {"alto": 2420.0, "medio": 1890.0, "baixo": 1510.0},
    "PR": {"alto": 2750.0, "medio": 2150.0, "baixo": 1750.0},
    "PE": {"alto": 2550.0, "medio": 2000.0, "baixo": 1600.0},
    "PI": {"alto": 2380.0, "medio": 1850.0, "baixo": 1490.0},
    "RJ": {"alto": 2850.0, "medio": 2250.0, "baixo": 1850.0},
    "RN": {"alto": 2440.0, "medio": 1900.0, "baixo": 1520.0},
    "RS": {"alto": 2700.0, "medio": 2100.0, "baixo": 1700.0},
    "RO": {"alto": 2420.0, "medio": 1900.0, "baixo": 1520.0},
    "RR": {"alto": 2380.0, "medio": 1850.0, "baixo": 1490.0},
    "SC": {"alto": 2800.0, "medio": 2200.0, "baixo": 1800.0},
    "SP": {"alto": 2900.0, "medio": 2300.0, "baixo": 1900.0},
    "SE": {"alto": 2400.0, "medio": 1880.0, "baixo": 1510.0},
    "TO": {"alto": 2450.0, "medio": 1900.0, "baixo": 1520.0},
}


class SimuladorInput(BaseModel):
    padrao: str = Field(..., description="Padrão de acabamento: baixo, medio, alto")
    metragem: float = Field(..., gt=0, description="Área construída em m²")
    uf: str = Field(..., min_length=2, max_length=2, description="Sigla do estado com 2 letras (ex: SC, SP)")


class SimuladorOutput(BaseModel):
    valor_estimado: float = Field(..., description="Valor total estimado da obra")
    custo_m2: float = Field(..., description="Custo do m² estimado para a UF e padrão")
    margem_financiamento: float = Field(..., description="Margem de financiamento sugerida (80% do valor total)")


def normalizar_padrao(padrao: str) -> str:
    """Normaliza o padrão de acabamento removendo acentos e convertendo para minúsculas."""
    norm = "".join(
        c for c in unicodedata.normalize("NFD", padrao.lower().strip())
        if unicodedata.category(c) != "Mn"
    )
    if "alto" in norm:
        return "alto"
    elif "baixo" in norm:
        return "baixo"
    else:
        return "medio"


@router.post("/calcular", response_model=SimuladorOutput)
async def calcular_simulacao(payload: SimuladorInput):
    """
    Endpoint público para cálculo de simulação paramétrica de custos.
    Retorna estimativa rápida baseada na metragem, UF e padrão de acabamento.
    """
    uf = payload.uf.upper().strip()
    padrao = normalizar_padrao(payload.padrao)

    # Busca o custo do m² por UF, com fallback para média nacional
    cub_uf = CUB_REFERENCIA.get(uf, {"alto": 2600.0, "medio": 2000.0, "baixo": 1600.0})
    custo_m2 = cub_uf.get(padrao, 2000.0)

    valor_estimado = payload.metragem * custo_m2
    # 80% do valor total estimado para a margem de financiamento do banco
    margem_financiamento = valor_estimado * 0.8

    return SimuladorOutput(
        valor_estimado=round(valor_estimado, 2),
        custo_m2=round(custo_m2, 2),
        margem_financiamento=round(margem_financiamento, 2)
    )
