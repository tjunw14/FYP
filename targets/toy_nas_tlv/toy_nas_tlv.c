#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

static int parse_tlv_payload(const uint8_t *data, size_t len) {
    size_t offset = 0;
    int score = 0;

    while (offset + 2 <= len) {
        uint8_t tag = data[offset++];
        uint8_t field_len = data[offset++];

        if (offset + field_len > len) {
            return -1;
        }

        const uint8_t *value = data + offset;

        switch (tag) {
        case 0x01:
            if (field_len == 1 && value[0] == 0x7f) {
                score += 3;
            }
            break;
        case 0x02:
            if (field_len >= 2 && value[0] == 0x13 && value[1] == 0x37) {
                score += 5;
            }
            break;
        case 0x7e:
            if (field_len >= 4 && value[0] == 'N' && value[1] == 'A' && value[2] == 'S') {
                score += 7;
            }
            break;
        default:
            score += tag & 1;
            break;
        }

        offset += field_len;
    }

    return score;
}

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (size < 2) {
        return 0;
    }

    uint8_t message_type = data[0];
    uint8_t payload_len = data[1];

    if ((size_t)payload_len > size - 2) {
        return 0;
    }

    const uint8_t *payload = data + 2;
    int score = parse_tlv_payload(payload, payload_len);

    if (message_type == 0x41 && payload_len >= 4 && score > 10) {
        /* Deliberate educational crash for AFL++ pipeline validation only. */
        abort();
    }

    return 0;
}

#ifndef __AFL_FUZZ_TESTCASE_LEN
int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: %s <input>\n", argv[0]);
        return 1;
    }

    FILE *fp = fopen(argv[1], "rb");
    if (!fp) {
        perror("fopen");
        return 1;
    }

    uint8_t buf[4096];
    size_t n = fread(buf, 1, sizeof(buf), fp);
    fclose(fp);

    LLVMFuzzerTestOneInput(buf, n);
    return 0;
}
#endif
