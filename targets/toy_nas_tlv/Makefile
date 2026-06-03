CC ?= afl-clang-fast
CFLAGS ?= -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer
TARGET = toy_nas_tlv
SEEDS = seeds
OUT = out

.PHONY: all clean fuzz fuzz-llm

all: $(TARGET)

$(TARGET): toy_nas_tlv.c
	$(CC) $(CFLAGS) -o $(TARGET) toy_nas_tlv.c

$(SEEDS):
	mkdir -p $(SEEDS)
	printf '\x01\x00' > $(SEEDS)/seed_001.bin
	printf '\x41\x04\x01\x01\x7f\x00' > $(SEEDS)/seed_002.bin
	printf '\x7e\x05\x7e\x03NAS' > $(SEEDS)/seed_003.bin

fuzz: all $(SEEDS)
	afl-fuzz -i $(SEEDS) -o $(OUT) -- ./$(TARGET) @@

fuzz-llm: all
	afl-fuzz -i seeds_llm -o out_llm -- ./$(TARGET) @@

clean:
	rm -f $(TARGET)
	rm -rf $(OUT) out_llm
