from chaoxing_agent._aes import encrypt_block, encrypt_cbc


def test_aes_block_encryption_matches_fips_197_vectors() -> None:
    plaintext = bytes.fromhex("00112233445566778899aabbccddeeff")
    vectors = (
        ("000102030405060708090a0b0c0d0e0f", "69c4e0d86a7b0430d8cdb78070b4c55a"),
        (
            "000102030405060708090a0b0c0d0e0f1011121314151617",
            "dda97ca4864cdfe06eaf70a0ec0d7191",
        ),
        (
            "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f",
            "8ea2b7ca516745bfeafc49904b496089",
        ),
    )
    for key, expected in vectors:
        assert encrypt_block(plaintext, bytes.fromhex(key)).hex() == expected


def test_aes_cbc_encryption_matches_nist_vector() -> None:
    key = bytes.fromhex("2b7e151628aed2a6abf7158809cf4f3c")
    initialization_vector = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
    plaintext = bytes.fromhex("6bc1bee22e409f96e93d7e117393172a")
    assert (
        encrypt_cbc(plaintext, key, initialization_vector).hex()
        == "7649abac8119b246cee98e9b12e9197d"
    )
