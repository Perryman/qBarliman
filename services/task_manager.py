from PySide6.QtCore import QObject, Signal, Slot

from services.scheme_execution_service import SchemeExecutionService, TaskResult
from utils.query_builder import QueryBuilder, SchemeQueryType
from models.scheme_document_data import SchemeDocumentData


class TaskManager(QObject):
    taskResultReady = Signal(TaskResult)  # Forward the result signal

    def __init__(self, scheme_execution_service: SchemeExecutionService, parent=None):
        super().__init__(parent)
        self.scheme_execution_service = scheme_execution_service
        self.query_builder = QueryBuilder()

        # Connect the query builder's signal to a *local* slot
        self.query_builder.queryBuilt.connect(self.handle_query_built)
        # Forward task results from the execution service
        self.scheme_execution_service.taskResultReady.connect(self.taskResultReady)

    @Slot(int, str, str)
    def run_test(self, test_index: int, input_text: str, expected_text: str):
        """Requests the execution of a single test case."""
        document_data = SchemeDocumentData(
            definition_text="",  # Definitions handled separately
            test_inputs=[input_text],
            test_expected=[expected_text],
        )
        self.query_builder.build_query(
            SchemeQueryType.TEST, (document_data, test_index + 1)
        )

    @Slot(str, SchemeQueryType)
    def handle_query_built(self, query: str, query_type: SchemeQueryType):
        """Handles the query string after it's been built."""
        if query_type == SchemeQueryType.TEST:
            # Extract test index from query.  Much cleaner approach.
            try:
                test_number_start = query.index("(query-val-test") + len("(query-val-test")
                test_number_str = query[test_number_start:].split(")")[0]
                test_index = int(test_number_str.strip()) -1 # Get the integer
                # Delegate execution to the SchemeExecutionService

                self.scheme_execution_service.execute_scheme_query(query, "test", test_index)
            except Exception as e:
                print(f"Could not handle query built. Error: {e}")