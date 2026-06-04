#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "core/ogs-core.h"
#include "nas/5gs/ogs-nas-5gs.h"

int ogs_nas_5gs_decode_registration_request(
    ogs_nas_5gs_message_t *message,
    ogs_pkbuf_t *pkbuf
);


/*
 * First Open5GS AFL++ harness.
 *
 * Target:
 *   ogs_nas_5gs_decode_registration_request()
 *
 * Input format:
 *   AFL++ input is treated as the body of a 5G NAS Registration Request.
 *
 * Note:
 *   This is a message-specific decoder harness, not a full NAS dispatcher harness.
 */

int main(int argc, char **argv)
{
    FILE *fp = NULL;
    uint8_t input[4096];
    size_t len = 0;

    ogs_pkbuf_t *pkbuf = NULL;
    ogs_nas_5gs_message_t message;

    if (argc != 2) {
        return 1;
    }

    fp = fopen(argv[1], "rb");
    if (!fp) {
        return 1;
    }

    len = fread(input, 1, sizeof(input), fp);
    fclose(fp);

    if (len == 0) {
        return 0;
    }

    memset(&message, 0, sizeof(message));

    ogs_pkbuf_init();

    pkbuf = ogs_pkbuf_alloc(NULL, (unsigned int)len);
    if (!pkbuf) {
        ogs_pkbuf_final();
        return 0;
    }

    ogs_pkbuf_put_data(pkbuf, input, (unsigned int)len);

    /*
     * We ignore the return value because AFL++ is interested in crashes,
     * sanitizer findings, and abnormal exits.
     */
    (void)ogs_nas_5gs_decode_registration_request(&message, pkbuf);

    ogs_pkbuf_free(pkbuf);
    ogs_pkbuf_final();

    return 0;
}
