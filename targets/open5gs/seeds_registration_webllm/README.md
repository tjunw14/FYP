# WebLLM-generated Open5GS registration seeds

This directory is used for binary AFL++ seed files generated from the WebLLM browser demo output.

The files should be generated using:

```bat
python scripts\import_webllm_hex_seeds.py --input reports\open5gs\phase5_webllm_demo\webllm_generated_seeds.txt --output targets\open5gs\seeds_registration_webllm --clean
```

The generated `.bin` files are used with the Open5GS Registration Request AFL++ harness.
