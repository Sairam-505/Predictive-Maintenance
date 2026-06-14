import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataLoader:
    """Load datasets from various sources and formats"""
    
    def __init__(self, data_path: str = "./data/raw"):
        self.data_path = Path(data_path)
    
    def load_bearing_dataset(self, dataset_name: str) -> pd.DataFrame:
        """
        Load bearing datasets (CWRU, Paderborn, IMS, XJTU, FEMTO)
        
        Args:
            dataset_name: "cwru", "paderborn", "ims", "xjtu", "femto"
        
        Returns:
            DataFrame with columns: [timestamp, signal, sensor_id, fault_type, rul]
        """
        if dataset_name.lower() == "cwru":
            return self._load_cwru()
        elif dataset_name.lower() == "paderborn":
            return self._load_paderborn()
        elif dataset_name.lower() == "ims":
            return self._load_ims()
        elif dataset_name.lower() == "xjtu":
            return self._load_xjtu()
        elif dataset_name.lower() == "femto":
            return self._load_femto()
        else:
            raise ValueError(f"Unknown dataset: {dataset_name}")
    
    def load_nasa_cmapss(self, subset: str = "FD001") -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Load NASA CMAPSS turbofan engine dataset
        
        Args:
            subset: "FD001", "FD002", "FD003", or "FD004"
        
        Returns:
            Tuple of (train_data, test_data)
        """
        # Load from .txt files
        train_file = self.data_path / f"train_{subset}.txt"
        test_file = self.data_path / f"test_{subset}.txt"
        rul_file = self.data_path / f"RUL_{subset}.txt"
        
        columns = (
            ["engine_id", "cycle"]
            + [f"operational_setting_{i}" for i in range(1, 4)]
            + [f"sensor_{i}" for i in range(1, 22)]
        )

        train_df = pd.read_csv(train_file, sep=r"\s+", header=None, names=columns)
        test_df = pd.read_csv(test_file, sep=r"\s+", header=None, names=columns)
        rul_df = pd.read_csv(rul_file, sep=r"\s+", header=None, names=["final_rul"])

        train_df["rul"] = train_df.groupby("engine_id")["cycle"].transform("max") - train_df["cycle"]
        test_max_cycles = test_df.groupby("engine_id")["cycle"].max().rename("max_observed_cycle")
        test_df = test_df.merge(test_max_cycles, on="engine_id")
        test_df = test_df.merge(
            rul_df.assign(engine_id=np.arange(1, len(rul_df) + 1)),
            on="engine_id",
            how="left",
        )
        test_df["rul"] = test_df["max_observed_cycle"] + test_df["final_rul"] - test_df["cycle"]
        test_df = test_df.drop(columns=["max_observed_cycle", "final_rul"])

        sensor_cols = [col for col in train_df.columns if col.startswith("sensor_")]
        train_df, test_df = self._minmax_normalize_pair(train_df, test_df, sensor_cols)
        
        logger.info(f"Loaded CMAPSS {subset}: {len(train_df)} train, {len(test_df)} test")
        return train_df, test_df
    
    def load_hydraulic_system(self) -> pd.DataFrame:
        """Load hydraulic system condition monitoring dataset"""
        csv_file = self._find_first_file("hydraulic", ["*.csv", "*.txt"])
        df = pd.read_csv(csv_file)
        if "rul" not in df.columns:
            target_candidates = [col for col in df.columns if "pump" in col.lower() and "condition" in col.lower()]
            if target_candidates:
                df = df.rename(columns={target_candidates[0]: "rul"})
        logger.info(f"Loaded hydraulic system data: {len(df)} samples")
        return df
    
    def _load_cwru(self) -> pd.DataFrame:
        """Load CWRU bearing dataset"""
        try:
            from scipy.io import loadmat
        except ImportError as exc:
            raise ImportError("scipy is required to load CWRU .mat files") from exc

        files = sorted((self.data_path / "cwru").glob("*.mat"))
        if not files:
            files = sorted(self.data_path.glob("**/*.mat"))
        if not files:
            raise FileNotFoundError("No CWRU .mat files found under data/raw/cwru")

        rows = []
        window_size = 24000
        for file_path in files:
            mat = loadmat(file_path)
            signal_key = next((key for key in mat if key.endswith("DE_time")), None)
            if signal_key is None:
                signal_key = next((key for key in mat if "DE" in key and "time" in key.lower()), None)
            if signal_key is None:
                logger.warning("Skipping %s because no drive-end signal key was found", file_path)
                continue

            signal = np.asarray(mat[signal_key]).ravel()
            fault_type = self._fault_from_filename(file_path.name)
            total_windows = max(1, len(signal) // window_size)
            for window_index, start in enumerate(range(0, len(signal) - window_size + 1, window_size)):
                window = signal[start:start + window_size]
                rows.append(
                    {
                        "timestamp": window_index,
                        "signal": window,
                        "sensor_id": "drive_end",
                        "fault_type": fault_type,
                        "rul": total_windows - window_index,
                        "source_file": file_path.name,
                    }
                )

        if not rows:
            raise ValueError("CWRU files were found, but no usable drive-end windows were extracted")
        df = pd.DataFrame(rows)
        logger.info(f"Loaded CWRU bearing data: {len(df)} windows")
        return df
    
    def _load_paderborn(self) -> pd.DataFrame:
        """Load Paderborn bearing dataset"""
        return self._load_generic_signal_csv("paderborn")
    
    def _load_ims(self) -> pd.DataFrame:
        """Load IMS bearing dataset"""
        files = sorted((self.data_path / "ims").glob("*.csv"))
        if not files:
            files = sorted((self.data_path / "ims").glob("*.txt"))
        if not files:
            raise FileNotFoundError("No IMS CSV/TXT files found under data/raw/ims")

        frames = []
        total = len(files)
        for index, file_path in enumerate(files):
            df = pd.read_csv(file_path, header=None)
            bearing_cols = [f"bearing_{i}" for i in range(1, min(4, df.shape[1]) + 1)]
            df = df.iloc[:, : len(bearing_cols)]
            df.columns = bearing_cols
            df["timestamp"] = index
            df["fault_type"] = "run_to_failure"
            df["rul"] = total - index
            df["source_file"] = file_path.name
            frames.append(df)

        result = pd.concat(frames, ignore_index=True)
        logger.info(f"Loaded IMS bearing data: {len(result)} samples")
        return result
    
    def _load_xjtu(self) -> pd.DataFrame:
        """Load XJTU bearing dataset"""
        return self._load_generic_signal_csv("xjtu")
    
    def _load_femto(self) -> pd.DataFrame:
        """Load FEMTO bearing dataset"""
        return self._load_generic_signal_csv("femto")

    def _load_generic_signal_csv(self, dataset_name: str) -> pd.DataFrame:
        dataset_dir = self.data_path / dataset_name
        files = sorted(dataset_dir.glob("*.csv"))
        if not files:
            raise FileNotFoundError(f"No CSV files found under {dataset_dir}")

        frames = []
        total = len(files)
        for index, file_path in enumerate(files):
            df = pd.read_csv(file_path)
            df["timestamp"] = index
            df["fault_type"] = self._fault_from_filename(file_path.name)
            df["rul"] = total - index
            df["source_file"] = file_path.name
            frames.append(df)
        result = pd.concat(frames, ignore_index=True)
        logger.info(f"Loaded {dataset_name} data: {len(result)} samples")
        return result

    def _find_first_file(self, subdir: str, patterns: list[str]) -> Path:
        search_roots = [self.data_path / subdir, self.data_path]
        for root in search_roots:
            for pattern in patterns:
                matches = sorted(root.glob(pattern))
                if matches:
                    return matches[0]
        raise FileNotFoundError(f"No files matching {patterns} found for {subdir}")

    def _fault_from_filename(self, filename: str) -> str:
        name = filename.lower()
        if "normal" in name or "healthy" in name:
            return "healthy"
        if "ir" in name or "inner" in name:
            return "inner_race"
        if "or" in name or "outer" in name:
            return "outer_race"
        if "_b" in name or "ball" in name:
            return "ball_fault"
        return "unknown_fault"

    def _minmax_normalize_pair(
        self,
        train_df: pd.DataFrame,
        test_df: pd.DataFrame,
        columns: list[str],
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        train_df = train_df.copy()
        test_df = test_df.copy()
        for col in columns:
            min_val = train_df[col].min()
            max_val = train_df[col].max()
            denominator = max_val - min_val + 1e-8
            train_df[col] = (train_df[col] - min_val) / denominator
            test_df[col] = (test_df[col] - min_val) / denominator
        return train_df, test_df

# Usage example:
if __name__ == "__main__":
    loader = DataLoader("./data/raw")
    
    # Load CMAPSS
    train, test = loader.load_nasa_cmapss("FD001")
    print(f"Train shape: {train.shape}, Test shape: {test.shape}")
    
    # Load hydraulic
    hyd_data = loader.load_hydraulic_system()
    print(f"Hydraulic data shape: {hyd_data.shape}")
