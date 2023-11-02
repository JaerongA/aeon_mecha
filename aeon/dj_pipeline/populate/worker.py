import datajoint as dj
from datajoint_utilities.dj_worker import DataJointWorker, ErrorLog, WorkerLog
from datajoint_utilities.dj_worker.worker_schema import is_djtable

from aeon.dj_pipeline import subject, acquisition, analysis, db_prefix, qc, report, tracking
from aeon.dj_pipeline.utils import streams_maker

streams = streams_maker.main()

__all__ = [
    "acquisition_worker",
    "mid_priority",
    "pyrat_worker",
    "streams_worker",
    "WorkerLog",
    "ErrorLog",
    "logger",
]

# ---- Some constants ----
logger = dj.logger
worker_schema_name = db_prefix + "worker"


# ---- Manage experiments for automated ingestion ----

schema = dj.Schema(worker_schema_name)


@schema
class AutomatedExperimentIngestion(dj.Manual):
    definition = """  # experiments to undergo automated ingestion
    -> acquisition.Experiment
    """


def ingest_epochs_chunks():
    """Ingest epochs and chunks for experiments specified in AutomatedExperimentIngestion."""
    experiment_names = AutomatedExperimentIngestion.fetch("experiment_name")
    for experiment_name in experiment_names:
        acquisition.Epoch.ingest_epochs(experiment_name)
        acquisition.Chunk.ingest_chunks(experiment_name)


def ingest_environment_visits():
    """Extract and insert complete visits for experiments specified in AutomatedExperimentIngestion."""
    experiment_names = AutomatedExperimentIngestion.fetch("experiment_name")
    analysis.ingest_environment_visits(experiment_names)


# ---- Define worker(s) ----
# configure a worker to process `acquisition`-related tasks
acquisition_worker = DataJointWorker(
    "acquisition_worker",
    worker_schema_name=worker_schema_name,
    db_prefix=db_prefix,
    run_duration=-1,
    sleep_duration=1200,
)
acquisition_worker(ingest_epochs_chunks)
acquisition_worker(acquisition.ExperimentLog)
acquisition_worker(acquisition.SubjectEnterExit)
acquisition_worker(acquisition.SubjectWeight)
acquisition_worker(acquisition.FoodPatchEvent)
acquisition_worker(acquisition.WheelState)

acquisition_worker(ingest_environment_visits)

# configure a worker to process mid-priority tasks
mid_priority = DataJointWorker(
    "mid_priority",
    worker_schema_name=worker_schema_name,
    db_prefix=db_prefix,
    run_duration=-1,
    sleep_duration=3600,
)

mid_priority(qc.CameraQC)
mid_priority(tracking.CameraTracking)
mid_priority(acquisition.FoodPatchWheel)
mid_priority(acquisition.WeightMeasurement)
mid_priority(acquisition.WeightMeasurementFiltered)

mid_priority(analysis.OverlapVisit)

mid_priority(analysis.VisitSubjectPosition)
mid_priority(analysis.VisitTimeDistribution)
mid_priority(analysis.VisitSummary)
mid_priority(analysis.VisitForagingBout)

# report tables
mid_priority(report.delete_outdated_plot_entries)
mid_priority(report.SubjectRewardRateDifference)
mid_priority(report.SubjectWheelTravelledDistance)
mid_priority(report.ExperimentTimeDistribution)
mid_priority(report.VisitDailySummaryPlot)

# configure a worker to handle pyrat sync
pyrat_worker = DataJointWorker(
    "pyrat_worker",
    worker_schema_name=worker_schema_name,
    db_prefix=db_prefix,
    run_duration=-1,
    sleep_duration=1200,
)

pyrat_worker(subject.CreatePyratIngestionTask)
pyrat_worker(subject.PyratIngestion)
pyrat_worker(subject.SubjectDetail)
pyrat_worker(subject.PyratCommentWeightProcedure)

# configure a worker to ingest all data streams
streams_worker = DataJointWorker(
    "streams_worker",
    worker_schema_name=worker_schema_name,
    db_prefix=db_prefix,
    run_duration=-1,
    sleep_duration=1200,
)

for attr in vars(streams).values():
    if is_djtable(attr, dj.user_tables.AutoPopulate):
        streams_worker(attr, max_calls=10)
