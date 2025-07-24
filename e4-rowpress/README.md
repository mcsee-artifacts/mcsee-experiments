# E4: Rowpress

## Preparation

Obtain a copy of our modified [Rowpress fork](https://github.com/mcsee-artifacts/rowpress) in which we improved the synchronization to make triggering bit flips faster and equipped the code to facilitate capturing data with the oscilloscope.

For the Rowpress data from the original work by Luo et al.[^1], we refer to the [rowpress_characterization_data.tar.gz](https://zenodo.org/records/7768005/files/rowpress_characterization_data.tar.gz?download=1) archive on Zenodo[^2]. 

> [!CAUTION]
> Extracting the Rowpress characterization data archive (105.9 GiB) requires around 1 TiB of disk space.

## Execution

Run Algo2 ([main-algo2.cpp](https://github.com/mcsee-artifacts/rowpress/blob/main/demonstration/main-algo2.cpp)) of the RowPress real system demonstration with 2 aggr. acts and `{1,2,4,8,16,32,64,80,128}` column reads. See the included [`README`](https://github.com/mcsee-artifacts/rowpress?tab=readme-ov-file#demonstration) for instructions on how to run the code. While running the code, take two 1 ms captures of each configuration with McSee.

>[!NOTE]
> There is no built-in way to run only a specific number of column reads, therefore the code lines [main-algo2.cpp:677+680](https://github.com/mcsee-artifacts/rowpress/blob/main/demonstration/main-algo2.cpp#L677) must be updated manually.

For convenience, we provide the captured data in `mcsee-data/e4-rowpress/raw.tar.zst` and the decoded data in `mcsee-data/e4-rowpress/decoded.tar.zst`.

## Analysis

> [!IMPORTANT]
> If you want to use the existing data, you must unpack first the `decoded.tar.zst` archive (located at `e4-rowpress/` in the mcsee-data repository) with
> ```
> zstd -d decoded.tar.zst --stdout | tar -xvf -
> ```

Run the `process.py` script by passing the directory of the decoded data:

```bash
python3 process.py ${MCSEE_DATA}/e4-rowpress/decoded/
```

where `${MCSEE_DATA}` is the path to the McSee data repository.


> [!NOTE]
> Instead of using our [DDR4 decoder](https://github.com/mcsee-artifacts/ddr4-decoder) supporting a more complete DDR4 command set, our analysis uses a simpler decoder that is integrated in the [`process.py`](analysis/process.py) script.

## Result

Run the Python3 script `plot.py`, which reads the `results_filtered.csv` that is generated during the analysis. This plotting script generates Fig. 9 of the paper.

[^1]: H. Luo et al., “RowPress: Amplifying Read Disturbance in Modern DRAM Chips,” in Proceedings of the 50th Annual International Symposium on Computer Architecture, Orlando FL USA: ACM, Jun. 2023, pp. 1–18. doi: 10.1145/3579371.3589063. Available: https://dl.acm.org/doi/10.1145/3579371.3589063.
[^2]: https://zenodo.org/records/7768005
