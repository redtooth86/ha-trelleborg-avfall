# Trelleborg Kretslopp och Vatten – Home Assistant

Visar när dina avfallskärl töms enligt ditt abonnemang hos Trelleborg Kretslopp och Vatten.
Du lägger själv in dina kärl och tömningsdagar – integrationen räknar sedan ut alla kommande
tömningar, även säsongsabonnemang som trädgårdsavfall.

> Inofficiell integration, inte kopplad till Trelleborgs kommun.

## Funktioner

- **En sensor per kärl** med datum för nästa tömning. Attribut: `days_until`, `upcoming`
  (kommande 5 datum), `interval_weeks`, `contents`, `season`.
- **Sensorn "Nästa tömning"** – nästa gång något kärl töms och vilka (`bins`).
- **Tömningskalender** som syns i Home Assistants kalendervy.
- Förinställningar för Trelleborgs abonnemang:
  - Fyrfack 370 L – Kärl 1 (var 14:e dag)
  - Fyrfack 370 L – Kärl 2 (var 4:e vecka)
  - Trädgårdsavfall 370 L (var 14:e dag, säsong v.12–47)
  - Matavfall, restavfall eller valfritt kärl
- Inställda och extra tömningar (t.ex. runt helgdagar) kan läggas in som datum.
- Kärl läggs till, ändras och tas bort i efterhand under **Konfigurera**.

## Installation

### HACS (rekommenderas)

1. HACS → ⋮ → **Anpassade arkiv** → lägg till `https://github.com/redtooth86/ha-trelleborg-avfall`, kategori **Integration**.
2. Installera **Trelleborg Kretslopp och Vatten** och starta om Home Assistant.

### Manuellt

Kopiera `custom_components/trelleborg_avfall` till `config/custom_components/` och starta om.

## Inställning

1. **Inställningar → Enheter och tjänster → Lägg till integration → Trelleborg Kretslopp och Vatten**.
2. Ange anläggningens adress.
3. Välj typ av kärl. Namn, intervall och säsong fylls i automatiskt.
4. Ange **ett datum då kärlet töms** – t.ex. senaste eller nästa tömning. Veckodag och
   vilka veckor tömning sker räknas ut från det datumet.
5. Lägg till fler kärl eller välj **Klar**.

### Exempel: Östergatan 42, Anderslöv

| Kärl | Typ | Intervall | Säsong | Ett tömningsdatum |
|------|-----|-----------|--------|-------------------|
| Kärl, 370 L fyrfack. Kärl 1 | Fyrfack – Kärl 1 | 2 veckor | – | ons 2026-11-04 |
| Kärl, 370 L fyrfack. Kärl 2 | Fyrfack – Kärl 2 | 4 veckor | – | tor 2026-11-19 |
| Kärl 370 L, trädgårdsavfall | Trädgårdsavfall | 2 veckor | v.12–47 | mån 2026-11-09 |

Integrationen ger då exakt samma datum som kommunens hämtschema (testat i
`tests/test_schedule.py`).

Datum för en tömning hittar du i tömningsschemat på Mina sidor eller i
Trelleborgs kommuns app/hämtkalender.

## Exempel

### Påminnelse kvällen före

```yaml
automation:
  - alias: "Påminnelse sopor"
    triggers:
      - trigger: time
        at: "19:00:00"
    conditions:
      - condition: template
        value_template: "{{ state_attr('sensor.ostergatan_42_anderslov_nasta_tomning', 'days_until') == 1 }}"
    actions:
      - action: notify.notify
        data:
          message: >
            Ställ ut {{ state_attr('sensor.ostergatan_42_anderslov_nasta_tomning', 'bins') | join(' och ') }} i kväll!
```

Entitets-id:n beror på adressen och kärlens namn – kontrollera dem under **Enheter och tjänster**.

### Kort i dashboarden

```yaml
type: entities
title: Sophämtning
entities:
  - entity: sensor.ostergatan_42_anderslov_karl_1_fyrfack_370_l
  - entity: sensor.ostergatan_42_anderslov_karl_2_fyrfack_370_l
  - entity: sensor.ostergatan_42_anderslov_tradgardsavfall_370_l
```

## Hur schemat räknas

Varje kärl töms var *N*:e vecka räknat från datumet du angav, bakåt och framåt i tiden.
Med säsong tas bara tömningar med i de ISO-veckor som ingår i säsongen; rytmen behålls över
vintern. Stämmer inte första tömningen på våren – ändra kärlet och ange det nya datumet.

## Utveckling

```bash
python -m unittest discover tests        # schemalogik
pip install pytest-homeassistant-custom-component
pytest                                   # hela integrationen i Home Assistant
```

## Licens

MIT
