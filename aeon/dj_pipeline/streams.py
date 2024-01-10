#----                     DO NOT MODIFY                ----
#---- THIS FILE IS AUTO-GENERATED BY `streams_maker.py` ----

import re
import datajoint as dj
import pandas as pd
from uuid import UUID

import aeon
from aeon.dj_pipeline import acquisition, get_schema_name
from aeon.io import api as io_api

schema = dj.Schema(get_schema_name("streams"))


@schema 
class StreamType(dj.Lookup):
    """Catalog of all steam types for the different device types used across Project Aeon. One StreamType corresponds to one reader class in `aeon.io.reader`. The combination of `stream_reader` and `stream_reader_kwargs` should fully specify the data loading routine for a particular device, using the `aeon.io.utils`."""

    definition = """  # Catalog of all stream types used across Project Aeon
    stream_type          : varchar(20)
    ---
    stream_reader        : varchar(256)     # name of the reader class found in `aeon_mecha` package (e.g. aeon.io.reader.Video)
    stream_reader_kwargs : longblob  # keyword arguments to instantiate the reader class
    stream_description='': varchar(256)
    stream_hash          : uuid    # hash of dict(stream_reader_kwargs, stream_reader=stream_reader)
    unique index (stream_hash)
    """


@schema 
class DeviceType(dj.Lookup):
    """Catalog of all device types used across Project Aeon."""

    definition = """  # Catalog of all device types used across Project Aeon
    device_type:             varchar(36)
    ---
    device_description='':   varchar(256)
    """

    class Stream(dj.Part):
        definition = """  # Data stream(s) associated with a particular device type
        -> master
        -> StreamType
        """


@schema 
class Device(dj.Lookup):
    definition = """  # Physical devices, of a particular type, identified by unique serial number
    device_serial_number: varchar(12)
    ---
    -> DeviceType
    """


@schema 
class SpinnakerVideoSource(dj.Manual):
        definition = f"""
        # spinnaker_video_source placement and operation for a particular time period, at a certain location, for a given experiment (auto-generated with aeon_mecha-unknown)
        -> acquisition.Experiment
        -> Device
        spinnaker_video_source_install_time  : datetime(6)   # time of the spinnaker_video_source placed and started operation at this position
        ---
        spinnaker_video_source_name          : varchar(36)
        """

        class Attribute(dj.Part):
            definition = """  # metadata/attributes (e.g. FPS, config, calibration, etc.) associated with this experimental device
            -> master
            attribute_name          : varchar(32)
            ---
            attribute_value=null    : longblob
            """

        class RemovalTime(dj.Part):
            definition = f"""
            -> master
            ---
            spinnaker_video_source_removal_time: datetime(6)  # time of the spinnaker_video_source being removed
            """


@schema 
class UndergroundFeeder(dj.Manual):
        definition = f"""
        # underground_feeder placement and operation for a particular time period, at a certain location, for a given experiment (auto-generated with aeon_mecha-unknown)
        -> acquisition.Experiment
        -> Device
        underground_feeder_install_time  : datetime(6)   # time of the underground_feeder placed and started operation at this position
        ---
        underground_feeder_name          : varchar(36)
        """

        class Attribute(dj.Part):
            definition = """  # metadata/attributes (e.g. FPS, config, calibration, etc.) associated with this experimental device
            -> master
            attribute_name          : varchar(32)
            ---
            attribute_value=null    : longblob
            """

        class RemovalTime(dj.Part):
            definition = f"""
            -> master
            ---
            underground_feeder_removal_time: datetime(6)  # time of the underground_feeder being removed
            """


@schema 
class WeightScale(dj.Manual):
        definition = f"""
        # weight_scale placement and operation for a particular time period, at a certain location, for a given experiment (auto-generated with aeon_mecha-unknown)
        -> acquisition.Experiment
        -> Device
        weight_scale_install_time  : datetime(6)   # time of the weight_scale placed and started operation at this position
        ---
        weight_scale_name          : varchar(36)
        """

        class Attribute(dj.Part):
            definition = """  # metadata/attributes (e.g. FPS, config, calibration, etc.) associated with this experimental device
            -> master
            attribute_name          : varchar(32)
            ---
            attribute_value=null    : longblob
            """

        class RemovalTime(dj.Part):
            definition = f"""
            -> master
            ---
            weight_scale_removal_time: datetime(6)  # time of the weight_scale being removed
            """


@schema 
class SpinnakerVideoSourceVideo(dj.Imported):
        definition = """  # Raw per-chunk Video data stream from SpinnakerVideoSource (auto-generated with aeon_mecha-unknown)
    -> SpinnakerVideoSource
    -> acquisition.Chunk
    ---
    sample_count: int      # number of data points acquired from this stream for a given chunk
    timestamps: longblob   # (datetime) timestamps of Video data
    hw_counter: longblob
    hw_timestamp: longblob
    """
        _stream_reader = aeon.io.reader.Video
        _stream_detail = {'stream_type': 'Video', 'stream_reader': 'aeon.io.reader.Video', 'stream_reader_kwargs': {'pattern': '{pattern}_*'}, 'stream_description': '', 'stream_hash': UUID('f51c6174-e0c4-a888-3a9d-6f97fb6a019b')}

        @property
        def key_source(self):
            f"""
            Only the combination of Chunk and SpinnakerVideoSource with overlapping time
            +  Chunk(s) that started after SpinnakerVideoSource install time and ended before SpinnakerVideoSource remove time
            +  Chunk(s) that started after SpinnakerVideoSource install time for SpinnakerVideoSource that are not yet removed
            """
            return (
                acquisition.Chunk * SpinnakerVideoSource.join(SpinnakerVideoSource.RemovalTime, left=True)
                & 'chunk_start >= spinnaker_video_source_install_time'
                & 'chunk_start < IFNULL(spinnaker_video_source_removal_time, "2200-01-01")'
            )

        def make(self, key):
            chunk_start, chunk_end, dir_type = (acquisition.Chunk & key).fetch1(
                "chunk_start", "chunk_end", "directory_type"
            )
            raw_data_dir = acquisition.Experiment.get_data_directory(key, directory_type=dir_type)

            device_name = (SpinnakerVideoSource & key).fetch1('spinnaker_video_source_name')

            stream = self._stream_reader(
                **{
                    k: v.format(**{k: device_name}) if k == "pattern" else v
                    for k, v in self._stream_detail["stream_reader_kwargs"].items()
                }
            )

            stream_data = io_api.load(
                root=raw_data_dir.as_posix(),
                reader=stream,
                start=pd.Timestamp(chunk_start),
                end=pd.Timestamp(chunk_end),
            )

            self.insert1(
                {
                    **key,
                    "sample_count": len(stream_data),
                    "timestamps": stream_data.index.values,
                    **{
                        re.sub(r"\([^)]*\)", "", c): stream_data[c].values
                        for c in stream.columns
                        if not c.startswith("_")
                    },
                },
                ignore_extra_fields=True,
            )


@schema 
class UndergroundFeederBeamBreak(dj.Imported):
        definition = """  # Raw per-chunk BeamBreak data stream from UndergroundFeeder (auto-generated with aeon_mecha-unknown)
    -> UndergroundFeeder
    -> acquisition.Chunk
    ---
    sample_count: int      # number of data points acquired from this stream for a given chunk
    timestamps: longblob   # (datetime) timestamps of BeamBreak data
    event: longblob
    """
        _stream_reader = aeon.io.reader.BitmaskEvent
        _stream_detail = {'stream_type': 'BeamBreak', 'stream_reader': 'aeon.io.reader.BitmaskEvent', 'stream_reader_kwargs': {'pattern': '{pattern}_32_*', 'value': 34, 'tag': 'PelletDetected'}, 'stream_description': '', 'stream_hash': UUID('ab975afc-c88d-2b66-d22b-65649b0ea5f0')}

        @property
        def key_source(self):
            f"""
            Only the combination of Chunk and UndergroundFeeder with overlapping time
            +  Chunk(s) that started after UndergroundFeeder install time and ended before UndergroundFeeder remove time
            +  Chunk(s) that started after UndergroundFeeder install time for UndergroundFeeder that are not yet removed
            """
            return (
                acquisition.Chunk * UndergroundFeeder.join(UndergroundFeeder.RemovalTime, left=True)
                & 'chunk_start >= underground_feeder_install_time'
                & 'chunk_start < IFNULL(underground_feeder_removal_time, "2200-01-01")'
            )

        def make(self, key):
            chunk_start, chunk_end, dir_type = (acquisition.Chunk & key).fetch1(
                "chunk_start", "chunk_end", "directory_type"
            )
            raw_data_dir = acquisition.Experiment.get_data_directory(key, directory_type=dir_type)

            device_name = (UndergroundFeeder & key).fetch1('underground_feeder_name')

            stream = self._stream_reader(
                **{
                    k: v.format(**{k: device_name}) if k == "pattern" else v
                    for k, v in self._stream_detail["stream_reader_kwargs"].items()
                }
            )

            stream_data = io_api.load(
                root=raw_data_dir.as_posix(),
                reader=stream,
                start=pd.Timestamp(chunk_start),
                end=pd.Timestamp(chunk_end),
            )

            self.insert1(
                {
                    **key,
                    "sample_count": len(stream_data),
                    "timestamps": stream_data.index.values,
                    **{
                        re.sub(r"\([^)]*\)", "", c): stream_data[c].values
                        for c in stream.columns
                        if not c.startswith("_")
                    },
                },
                ignore_extra_fields=True,
            )


@schema 
class UndergroundFeederDeliverPellet(dj.Imported):
        definition = """  # Raw per-chunk DeliverPellet data stream from UndergroundFeeder (auto-generated with aeon_mecha-unknown)
    -> UndergroundFeeder
    -> acquisition.Chunk
    ---
    sample_count: int      # number of data points acquired from this stream for a given chunk
    timestamps: longblob   # (datetime) timestamps of DeliverPellet data
    event: longblob
    """
        _stream_reader = aeon.io.reader.BitmaskEvent
        _stream_detail = {'stream_type': 'DeliverPellet', 'stream_reader': 'aeon.io.reader.BitmaskEvent', 'stream_reader_kwargs': {'pattern': '{pattern}_35_*', 'value': 128, 'tag': 'TriggerPellet'}, 'stream_description': '', 'stream_hash': UUID('09099227-ab3c-1f71-239e-4c6f017de1fd')}

        @property
        def key_source(self):
            f"""
            Only the combination of Chunk and UndergroundFeeder with overlapping time
            +  Chunk(s) that started after UndergroundFeeder install time and ended before UndergroundFeeder remove time
            +  Chunk(s) that started after UndergroundFeeder install time for UndergroundFeeder that are not yet removed
            """
            return (
                acquisition.Chunk * UndergroundFeeder.join(UndergroundFeeder.RemovalTime, left=True)
                & 'chunk_start >= underground_feeder_install_time'
                & 'chunk_start < IFNULL(underground_feeder_removal_time, "2200-01-01")'
            )

        def make(self, key):
            chunk_start, chunk_end, dir_type = (acquisition.Chunk & key).fetch1(
                "chunk_start", "chunk_end", "directory_type"
            )
            raw_data_dir = acquisition.Experiment.get_data_directory(key, directory_type=dir_type)

            device_name = (UndergroundFeeder & key).fetch1('underground_feeder_name')

            stream = self._stream_reader(
                **{
                    k: v.format(**{k: device_name}) if k == "pattern" else v
                    for k, v in self._stream_detail["stream_reader_kwargs"].items()
                }
            )

            stream_data = io_api.load(
                root=raw_data_dir.as_posix(),
                reader=stream,
                start=pd.Timestamp(chunk_start),
                end=pd.Timestamp(chunk_end),
            )

            self.insert1(
                {
                    **key,
                    "sample_count": len(stream_data),
                    "timestamps": stream_data.index.values,
                    **{
                        re.sub(r"\([^)]*\)", "", c): stream_data[c].values
                        for c in stream.columns
                        if not c.startswith("_")
                    },
                },
                ignore_extra_fields=True,
            )


@schema 
class UndergroundFeederDepletionState(dj.Imported):
        definition = """  # Raw per-chunk DepletionState data stream from UndergroundFeeder (auto-generated with aeon_mecha-unknown)
    -> UndergroundFeeder
    -> acquisition.Chunk
    ---
    sample_count: int      # number of data points acquired from this stream for a given chunk
    timestamps: longblob   # (datetime) timestamps of DepletionState data
    threshold: longblob
    offset: longblob
    rate: longblob
    """
        _stream_reader = aeon.io.reader.Csv
        _stream_detail = {'stream_type': 'DepletionState', 'stream_reader': 'aeon.io.reader.Csv', 'stream_reader_kwargs': {'pattern': '{pattern}_*', 'columns': ['threshold', 'offset', 'rate'], 'extension': 'csv', 'dtype': None}, 'stream_description': '', 'stream_hash': UUID('a944b719-c723-08f8-b695-7be616e57bd5')}

        @property
        def key_source(self):
            f"""
            Only the combination of Chunk and UndergroundFeeder with overlapping time
            +  Chunk(s) that started after UndergroundFeeder install time and ended before UndergroundFeeder remove time
            +  Chunk(s) that started after UndergroundFeeder install time for UndergroundFeeder that are not yet removed
            """
            return (
                acquisition.Chunk * UndergroundFeeder.join(UndergroundFeeder.RemovalTime, left=True)
                & 'chunk_start >= underground_feeder_install_time'
                & 'chunk_start < IFNULL(underground_feeder_removal_time, "2200-01-01")'
            )

        def make(self, key):
            chunk_start, chunk_end, dir_type = (acquisition.Chunk & key).fetch1(
                "chunk_start", "chunk_end", "directory_type"
            )
            raw_data_dir = acquisition.Experiment.get_data_directory(key, directory_type=dir_type)

            device_name = (UndergroundFeeder & key).fetch1('underground_feeder_name')

            stream = self._stream_reader(
                **{
                    k: v.format(**{k: device_name}) if k == "pattern" else v
                    for k, v in self._stream_detail["stream_reader_kwargs"].items()
                }
            )

            stream_data = io_api.load(
                root=raw_data_dir.as_posix(),
                reader=stream,
                start=pd.Timestamp(chunk_start),
                end=pd.Timestamp(chunk_end),
            )

            self.insert1(
                {
                    **key,
                    "sample_count": len(stream_data),
                    "timestamps": stream_data.index.values,
                    **{
                        re.sub(r"\([^)]*\)", "", c): stream_data[c].values
                        for c in stream.columns
                        if not c.startswith("_")
                    },
                },
                ignore_extra_fields=True,
            )


@schema 
class UndergroundFeederEncoder(dj.Imported):
        definition = """  # Raw per-chunk Encoder data stream from UndergroundFeeder (auto-generated with aeon_mecha-unknown)
    -> UndergroundFeeder
    -> acquisition.Chunk
    ---
    sample_count: int      # number of data points acquired from this stream for a given chunk
    timestamps: longblob   # (datetime) timestamps of Encoder data
    angle: longblob
    intensity: longblob
    """
        _stream_reader = aeon.io.reader.Encoder
        _stream_detail = {'stream_type': 'Encoder', 'stream_reader': 'aeon.io.reader.Encoder', 'stream_reader_kwargs': {'pattern': '{pattern}_90_*'}, 'stream_description': '', 'stream_hash': UUID('f96b0b26-26f6-5ff6-b3c7-5aa5adc00c1a')}

        @property
        def key_source(self):
            f"""
            Only the combination of Chunk and UndergroundFeeder with overlapping time
            +  Chunk(s) that started after UndergroundFeeder install time and ended before UndergroundFeeder remove time
            +  Chunk(s) that started after UndergroundFeeder install time for UndergroundFeeder that are not yet removed
            """
            return (
                acquisition.Chunk * UndergroundFeeder.join(UndergroundFeeder.RemovalTime, left=True)
                & 'chunk_start >= underground_feeder_install_time'
                & 'chunk_start < IFNULL(underground_feeder_removal_time, "2200-01-01")'
            )

        def make(self, key):
            chunk_start, chunk_end, dir_type = (acquisition.Chunk & key).fetch1(
                "chunk_start", "chunk_end", "directory_type"
            )
            raw_data_dir = acquisition.Experiment.get_data_directory(key, directory_type=dir_type)

            device_name = (UndergroundFeeder & key).fetch1('underground_feeder_name')

            stream = self._stream_reader(
                **{
                    k: v.format(**{k: device_name}) if k == "pattern" else v
                    for k, v in self._stream_detail["stream_reader_kwargs"].items()
                }
            )

            stream_data = io_api.load(
                root=raw_data_dir.as_posix(),
                reader=stream,
                start=pd.Timestamp(chunk_start),
                end=pd.Timestamp(chunk_end),
            )

            self.insert1(
                {
                    **key,
                    "sample_count": len(stream_data),
                    "timestamps": stream_data.index.values,
                    **{
                        re.sub(r"\([^)]*\)", "", c): stream_data[c].values
                        for c in stream.columns
                        if not c.startswith("_")
                    },
                },
                ignore_extra_fields=True,
            )


@schema 
class UndergroundFeederManualDelivery(dj.Imported):
        definition = """  # Raw per-chunk ManualDelivery data stream from UndergroundFeeder (auto-generated with aeon_mecha-unknown)
    -> UndergroundFeeder
    -> acquisition.Chunk
    ---
    sample_count: int      # number of data points acquired from this stream for a given chunk
    timestamps: longblob   # (datetime) timestamps of ManualDelivery data
    manual_delivery: longblob
    """
        _stream_reader = aeon.io.reader.Harp
        _stream_detail = {'stream_type': 'ManualDelivery', 'stream_reader': 'aeon.io.reader.Harp', 'stream_reader_kwargs': {'pattern': '{pattern}_*', 'columns': ['manual_delivery'], 'extension': 'bin'}, 'stream_description': '', 'stream_hash': UUID('98ce23d4-01c5-a848-dd6b-8b284c323fb0')}

        @property
        def key_source(self):
            f"""
            Only the combination of Chunk and UndergroundFeeder with overlapping time
            +  Chunk(s) that started after UndergroundFeeder install time and ended before UndergroundFeeder remove time
            +  Chunk(s) that started after UndergroundFeeder install time for UndergroundFeeder that are not yet removed
            """
            return (
                acquisition.Chunk * UndergroundFeeder.join(UndergroundFeeder.RemovalTime, left=True)
                & 'chunk_start >= underground_feeder_install_time'
                & 'chunk_start < IFNULL(underground_feeder_removal_time, "2200-01-01")'
            )

        def make(self, key):
            chunk_start, chunk_end, dir_type = (acquisition.Chunk & key).fetch1(
                "chunk_start", "chunk_end", "directory_type"
            )
            raw_data_dir = acquisition.Experiment.get_data_directory(key, directory_type=dir_type)

            device_name = (UndergroundFeeder & key).fetch1('underground_feeder_name')

            stream = self._stream_reader(
                **{
                    k: v.format(**{k: device_name}) if k == "pattern" else v
                    for k, v in self._stream_detail["stream_reader_kwargs"].items()
                }
            )

            stream_data = io_api.load(
                root=raw_data_dir.as_posix(),
                reader=stream,
                start=pd.Timestamp(chunk_start),
                end=pd.Timestamp(chunk_end),
            )

            self.insert1(
                {
                    **key,
                    "sample_count": len(stream_data),
                    "timestamps": stream_data.index.values,
                    **{
                        re.sub(r"\([^)]*\)", "", c): stream_data[c].values
                        for c in stream.columns
                        if not c.startswith("_")
                    },
                },
                ignore_extra_fields=True,
            )


@schema 
class UndergroundFeederMissedPellet(dj.Imported):
        definition = """  # Raw per-chunk MissedPellet data stream from UndergroundFeeder (auto-generated with aeon_mecha-unknown)
    -> UndergroundFeeder
    -> acquisition.Chunk
    ---
    sample_count: int      # number of data points acquired from this stream for a given chunk
    timestamps: longblob   # (datetime) timestamps of MissedPellet data
    missed_pellet: longblob
    """
        _stream_reader = aeon.io.reader.Harp
        _stream_detail = {'stream_type': 'MissedPellet', 'stream_reader': 'aeon.io.reader.Harp', 'stream_reader_kwargs': {'pattern': '{pattern}_*', 'columns': ['missed_pellet'], 'extension': 'bin'}, 'stream_description': '', 'stream_hash': UUID('2fa12bbc-3207-dddc-f6ee-b79c55b6d9a2')}

        @property
        def key_source(self):
            f"""
            Only the combination of Chunk and UndergroundFeeder with overlapping time
            +  Chunk(s) that started after UndergroundFeeder install time and ended before UndergroundFeeder remove time
            +  Chunk(s) that started after UndergroundFeeder install time for UndergroundFeeder that are not yet removed
            """
            return (
                acquisition.Chunk * UndergroundFeeder.join(UndergroundFeeder.RemovalTime, left=True)
                & 'chunk_start >= underground_feeder_install_time'
                & 'chunk_start < IFNULL(underground_feeder_removal_time, "2200-01-01")'
            )

        def make(self, key):
            chunk_start, chunk_end, dir_type = (acquisition.Chunk & key).fetch1(
                "chunk_start", "chunk_end", "directory_type"
            )
            raw_data_dir = acquisition.Experiment.get_data_directory(key, directory_type=dir_type)

            device_name = (UndergroundFeeder & key).fetch1('underground_feeder_name')

            stream = self._stream_reader(
                **{
                    k: v.format(**{k: device_name}) if k == "pattern" else v
                    for k, v in self._stream_detail["stream_reader_kwargs"].items()
                }
            )

            stream_data = io_api.load(
                root=raw_data_dir.as_posix(),
                reader=stream,
                start=pd.Timestamp(chunk_start),
                end=pd.Timestamp(chunk_end),
            )

            self.insert1(
                {
                    **key,
                    "sample_count": len(stream_data),
                    "timestamps": stream_data.index.values,
                    **{
                        re.sub(r"\([^)]*\)", "", c): stream_data[c].values
                        for c in stream.columns
                        if not c.startswith("_")
                    },
                },
                ignore_extra_fields=True,
            )


@schema 
class UndergroundFeederRetriedDelivery(dj.Imported):
        definition = """  # Raw per-chunk RetriedDelivery data stream from UndergroundFeeder (auto-generated with aeon_mecha-unknown)
    -> UndergroundFeeder
    -> acquisition.Chunk
    ---
    sample_count: int      # number of data points acquired from this stream for a given chunk
    timestamps: longblob   # (datetime) timestamps of RetriedDelivery data
    retried_delivery: longblob
    """
        _stream_reader = aeon.io.reader.Harp
        _stream_detail = {'stream_type': 'RetriedDelivery', 'stream_reader': 'aeon.io.reader.Harp', 'stream_reader_kwargs': {'pattern': '{pattern}_*', 'columns': ['retried_delivery'], 'extension': 'bin'}, 'stream_description': '', 'stream_hash': UUID('62f23eab-4469-5740-dfa0-6f1aa754de8e')}

        @property
        def key_source(self):
            f"""
            Only the combination of Chunk and UndergroundFeeder with overlapping time
            +  Chunk(s) that started after UndergroundFeeder install time and ended before UndergroundFeeder remove time
            +  Chunk(s) that started after UndergroundFeeder install time for UndergroundFeeder that are not yet removed
            """
            return (
                acquisition.Chunk * UndergroundFeeder.join(UndergroundFeeder.RemovalTime, left=True)
                & 'chunk_start >= underground_feeder_install_time'
                & 'chunk_start < IFNULL(underground_feeder_removal_time, "2200-01-01")'
            )

        def make(self, key):
            chunk_start, chunk_end, dir_type = (acquisition.Chunk & key).fetch1(
                "chunk_start", "chunk_end", "directory_type"
            )
            raw_data_dir = acquisition.Experiment.get_data_directory(key, directory_type=dir_type)

            device_name = (UndergroundFeeder & key).fetch1('underground_feeder_name')

            stream = self._stream_reader(
                **{
                    k: v.format(**{k: device_name}) if k == "pattern" else v
                    for k, v in self._stream_detail["stream_reader_kwargs"].items()
                }
            )

            stream_data = io_api.load(
                root=raw_data_dir.as_posix(),
                reader=stream,
                start=pd.Timestamp(chunk_start),
                end=pd.Timestamp(chunk_end),
            )

            self.insert1(
                {
                    **key,
                    "sample_count": len(stream_data),
                    "timestamps": stream_data.index.values,
                    **{
                        re.sub(r"\([^)]*\)", "", c): stream_data[c].values
                        for c in stream.columns
                        if not c.startswith("_")
                    },
                },
                ignore_extra_fields=True,
            )


@schema 
class WeightScaleWeightFiltered(dj.Imported):
        definition = """  # Raw per-chunk WeightFiltered data stream from WeightScale (auto-generated with aeon_mecha-unknown)
    -> WeightScale
    -> acquisition.Chunk
    ---
    sample_count: int      # number of data points acquired from this stream for a given chunk
    timestamps: longblob   # (datetime) timestamps of WeightFiltered data
    weight: longblob
    stability: longblob
    """
        _stream_reader = aeon.io.reader.Harp
        _stream_detail = {'stream_type': 'WeightFiltered', 'stream_reader': 'aeon.io.reader.Harp', 'stream_reader_kwargs': {'pattern': '{pattern}_202*', 'columns': ['weight(g)', 'stability'], 'extension': 'bin'}, 'stream_description': '', 'stream_hash': UUID('bd135a97-1161-3dd3-5ca3-e5d342485728')}

        @property
        def key_source(self):
            f"""
            Only the combination of Chunk and WeightScale with overlapping time
            +  Chunk(s) that started after WeightScale install time and ended before WeightScale remove time
            +  Chunk(s) that started after WeightScale install time for WeightScale that are not yet removed
            """
            return (
                acquisition.Chunk * WeightScale.join(WeightScale.RemovalTime, left=True)
                & 'chunk_start >= weight_scale_install_time'
                & 'chunk_start < IFNULL(weight_scale_removal_time, "2200-01-01")'
            )

        def make(self, key):
            chunk_start, chunk_end, dir_type = (acquisition.Chunk & key).fetch1(
                "chunk_start", "chunk_end", "directory_type"
            )
            raw_data_dir = acquisition.Experiment.get_data_directory(key, directory_type=dir_type)

            device_name = (WeightScale & key).fetch1('weight_scale_name')

            stream = self._stream_reader(
                **{
                    k: v.format(**{k: device_name}) if k == "pattern" else v
                    for k, v in self._stream_detail["stream_reader_kwargs"].items()
                }
            )

            stream_data = io_api.load(
                root=raw_data_dir.as_posix(),
                reader=stream,
                start=pd.Timestamp(chunk_start),
                end=pd.Timestamp(chunk_end),
            )

            self.insert1(
                {
                    **key,
                    "sample_count": len(stream_data),
                    "timestamps": stream_data.index.values,
                    **{
                        re.sub(r"\([^)]*\)", "", c): stream_data[c].values
                        for c in stream.columns
                        if not c.startswith("_")
                    },
                },
                ignore_extra_fields=True,
            )


@schema 
class WeightScaleWeightRaw(dj.Imported):
        definition = """  # Raw per-chunk WeightRaw data stream from WeightScale (auto-generated with aeon_mecha-unknown)
    -> WeightScale
    -> acquisition.Chunk
    ---
    sample_count: int      # number of data points acquired from this stream for a given chunk
    timestamps: longblob   # (datetime) timestamps of WeightRaw data
    weight: longblob
    stability: longblob
    """
        _stream_reader = aeon.io.reader.Harp
        _stream_detail = {'stream_type': 'WeightRaw', 'stream_reader': 'aeon.io.reader.Harp', 'stream_reader_kwargs': {'pattern': '{pattern}_200*', 'columns': ['weight(g)', 'stability'], 'extension': 'bin'}, 'stream_description': '', 'stream_hash': UUID('0d27b1af-e78b-d889-62c0-41a20df6a015')}

        @property
        def key_source(self):
            f"""
            Only the combination of Chunk and WeightScale with overlapping time
            +  Chunk(s) that started after WeightScale install time and ended before WeightScale remove time
            +  Chunk(s) that started after WeightScale install time for WeightScale that are not yet removed
            """
            return (
                acquisition.Chunk * WeightScale.join(WeightScale.RemovalTime, left=True)
                & 'chunk_start >= weight_scale_install_time'
                & 'chunk_start < IFNULL(weight_scale_removal_time, "2200-01-01")'
            )

        def make(self, key):
            chunk_start, chunk_end, dir_type = (acquisition.Chunk & key).fetch1(
                "chunk_start", "chunk_end", "directory_type"
            )
            raw_data_dir = acquisition.Experiment.get_data_directory(key, directory_type=dir_type)

            device_name = (WeightScale & key).fetch1('weight_scale_name')

            stream = self._stream_reader(
                **{
                    k: v.format(**{k: device_name}) if k == "pattern" else v
                    for k, v in self._stream_detail["stream_reader_kwargs"].items()
                }
            )

            stream_data = io_api.load(
                root=raw_data_dir.as_posix(),
                reader=stream,
                start=pd.Timestamp(chunk_start),
                end=pd.Timestamp(chunk_end),
            )

            self.insert1(
                {
                    **key,
                    "sample_count": len(stream_data),
                    "timestamps": stream_data.index.values,
                    **{
                        re.sub(r"\([^)]*\)", "", c): stream_data[c].values
                        for c in stream.columns
                        if not c.startswith("_")
                    },
                },
                ignore_extra_fields=True,
            )


