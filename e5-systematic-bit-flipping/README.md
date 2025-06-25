# E5: Systematic Bit Flipping

The [README](./code/README.md) in the `code/` directory explains how to set up the experiment and analyze the results. Adapt the [`code/runner.sh`](./code/runner.sh) script depending on your environment.

We provide the oscilloscope traces of the different experiment configurations in the `mcsee-data` repository:

```
mcsee-data
| 
├── e5-systematic-bit-flipping
   ├── amd_zen4
   │   ├── 1rk_4bg_4bk
   │   ├── 1rk_8bg_4bk
   │   ├── 2rk_8bg_4bk
   │   └── 2rk_8bg_4bk.tar.gz
   └── intel_raptor_lake
      ├── 20230404_095356_ee-tik-cn121_DIMM=501_raptorlake_8bg_4bk_1rk_0xc3200=0
      ├── 20230404_142100_ee-tik-cn121_DIMM=523_raptor_lake_4bg_4bk_1rk
      ├── 20230405_175847_ee-tik-cn121_DIMM=523_raptor_lake_4bg_4bk_1rk
      ├── 20230411_160313_ee-tik-cn121_DIMM=526_raptor_lake_2rk_8bg_4bk_subch_0xc3200=0
      └── 20230411_174105_ee-tik-cn121_DIMM=526_raptor_lake_2rk_8bg_4bk_rank=22+16=const
```
