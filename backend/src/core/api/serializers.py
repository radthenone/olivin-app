from rest_framework import serializers


class MoneySerializer(serializers.Serializer):
    """Kwota jako para: liczba całkowita groszy i kod waluty (ADR 0009).

    Kwota w API nie jest gołą liczbą ani łańcuchem z przecinkiem: klient
    dostaje tę samą parę, którą backend trzyma w `common.money.Money`, więc
    nigdzie po drodze nie powstaje liczba zmiennoprzecinkowa.
    """

    amount = serializers.IntegerField(
        read_only=True,
        help_text="Kwota w najmniejszej jednostce waluty (grosze)",
    )
    currency = serializers.CharField(
        read_only=True,
        help_text="Kod waluty ISO 4217",
    )
