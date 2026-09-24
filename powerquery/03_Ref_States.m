// Reference table: Brazilian state codes to names and regions.
// Used for maps (full names geocode more reliably) and for row-level security by region.
#table(
    type table [StateCode = text, StateName = text, Region = text],
    {
        {"AC", "Acre", "North"},            {"AP", "Amapá", "North"},
        {"AM", "Amazonas", "North"},        {"PA", "Pará", "North"},
        {"RO", "Rondônia", "North"},        {"RR", "Roraima", "North"},
        {"TO", "Tocantins", "North"},
        {"AL", "Alagoas", "Northeast"},     {"BA", "Bahia", "Northeast"},
        {"CE", "Ceará", "Northeast"},       {"MA", "Maranhão", "Northeast"},
        {"PB", "Paraíba", "Northeast"},     {"PE", "Pernambuco", "Northeast"},
        {"PI", "Piauí", "Northeast"},       {"RN", "Rio Grande do Norte", "Northeast"},
        {"SE", "Sergipe", "Northeast"},
        {"DF", "Distrito Federal", "Center-West"}, {"GO", "Goiás", "Center-West"},
        {"MT", "Mato Grosso", "Center-West"},      {"MS", "Mato Grosso do Sul", "Center-West"},
        {"ES", "Espírito Santo", "Southeast"},     {"MG", "Minas Gerais", "Southeast"},
        {"RJ", "Rio de Janeiro", "Southeast"},     {"SP", "São Paulo", "Southeast"},
        {"PR", "Paraná", "South"},          {"RS", "Rio Grande do Sul", "South"},
        {"SC", "Santa Catarina", "South"}
    }
)
