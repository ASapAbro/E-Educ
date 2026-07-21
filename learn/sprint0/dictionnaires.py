from conditions import verifier_note

etudiant = {
    "nom": "abro",
    "age": 25,
    "notes": [12, 18, 15, 0, 13, 25]
}
print(f"l'etudiant {etudiant['nom']} a {etudiant['age']} ans et ses notes sont : {etudiant['notes']}")

for note in etudiant["notes"]:
    verifier_note(note)