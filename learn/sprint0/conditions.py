def verifier_note(note):
    if  0 <= note <= 20:
        print("la note est valide")
    else:
        print("la note est invalide")

if __name__ == "__main__":
    verifier_note(20)