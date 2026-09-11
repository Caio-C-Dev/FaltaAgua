# Nomes canônicos — devem bater EXATAMENTE com app/lib/data/cities.dart,
# porque o tópico FCM é derivado daqui via slug.city_topic().
# A detecção no texto ignora acento, caixa e pontuação (ver classifier.py),
# então não é preciso listar variantes como "ribeirao das neves".
CIDADES_CANONICAS = [
    "Belo Horizonte",
    "Contagem",
    "Betim",
    "Santa Luzia",
    "Ribeirão das Neves",
    "Sabará",
    "Nova Lima",
    "Confins",
    "Ibirité",
    "Vespasiano",
    "Lagoa Santa",
    "Pedro Leopoldo",
    "Caeté",
]

# Apelidos usados em manchete que não são o nome canônico da cidade.
# Checados depois dos marcadores regionais, então "Grande BH" continua
# expandindo para todas as cidades em vez de virar só Belo Horizonte.
APELIDOS_CIDADES = {
    "bh": "Belo Horizonte",
    "beagá": "Belo Horizonte",
}

# Quando a notícia fala da região como um todo, o alerta vale para todas as cidades.
MARCADORES_REGIONAIS = [
    "grande bh",
    "grande belo horizonte",
    "região metropolitana",
    "rmbh",
]

# Todas as listas abaixo são comparadas com acento/caixa/pontuação ignorados,
# então basta escrever a forma acentuada — "sem água" também casa "SEM AGUA".
KEYWORDS_ALERTA = [
    "falta de água",
    "sem água",
    "abastecimento suspenso",
    "interrupção no abastecimento",
    "sem fornecimento de água",
    "desabastecimento",
]

KEYWORDS_RETORNO = [
    "abastecimento normalizado",
    "abastecimento restabelecido",
    "água volta",
    "volta a água",
    "retorno do abastecimento",
    "fornecimento restabelecido",
]

# Descartam ALERTAS que falam de manutenção ainda não ocorrida.
# Cuidado ao ampliar: deixar de avisar é pior do que avisar demais, e termos
# genéricos como "previsto" aparecem em notícias de falta de água real
# ("previsão de normalização às 18h"), derrubando o alerta por engano.
KEYWORDS_NEGATIVAS = [
    "será realizada",
    "vai realizar manutenção",
    "manutenção programada para",
    "previsão de interrupção",
]

QUERIES_GOOGLE_NEWS = [
    '"falta de água" "belo horizonte"',
    '"falta de água" copasa bh',
    '"sem água" "belo horizonte"',
    '"abastecimento" copasa',
    '"desabastecimento" bh',
]
