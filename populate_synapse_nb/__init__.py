# Any lines containging 'PopulateAzureSynapseNotebook' will not be copied to the notebook.
import copy                                 # used within PopulateAzureSynapseNotebook
from datetime import datetime, timezone     # used within PopulateAzureSynapseNotebook
import json                                 # used within PopulateAzureSynapseNotebook
from pathlib import Path                    # used within PopulateAzureSynapseNotebook


class PopulateAzureSynapseNotebook:
    """
    A class used to populate an Azure Synapse Notebook with the contents from another Python source file.
    This allows code development in a dedicated IDE rather than via the web IDE.
    """

    def __init__(self, source_path=None, destination_path=None):
        """
        Initialize the class with the source path and destination path.
        :param source_path: str, Path, optional. If none, the file containing this code will be used.
        :param destination_path: str, Path, optional. If none, use the .json equivalent of this file.
        """
        if not source_path:
            # This file will be used if no source is provided.
            source_path = Path(__file__)
        self.source_path = Path(source_path)
        if not destination_path:
            # If no destination is provided, it will be an equivalent json file in the same directory.
            destination_name = self.source_path.stem + '.json'
            destination_path = self.source_path.parent / destination_name
        self.destination_path = Path(destination_path)
        if not self.source_path.exists():
            raise ValueError('A valid source path must be provided.')
        if not self.destination_path.exists():
            raise ValueError('A valid destination path must be provided. This must be an existing Azure Synapse Analyics notebook.')

    def run(self, force=False):
        """
        Copy the contents of the source file to the destination Azure Synapse Notebook.
        """
        if not force and not self._confirm_action():
            print('Aborted')
            return
        lines_to_insert = self._read_source()
        lines_to_insert = self._remove_self_references(lines_to_insert)
        lines_to_insert = self._remove_edge_blanks(lines_to_insert)
        lines_to_insert = self._add_log(lines_to_insert)
        notebook_json = self._read_destination()
        notebook_json = self._insert_source_to_json(notebook_json, lines_to_insert)
        self._save_destination(notebook_json)

    def _confirm_action(self):
        message = "\n\n================================\n\n"
        message += "The contents of the notebook will be updated as follows:\n\n"
        message += f"SOURCE:         {self.source_path.name}\n"
        message += f"DESTINATION:    {self.destination_path.name}\n\n."
        print(message)
        user_input = input('Type "X" to confirm:\n')
        return user_input.upper() == 'X'

    def _read_source(self):
        with open(self.source_path, 'r') as file:
            source_lines = file.readlines()
        lines_to_insert = []
        for line in source_lines:
            if line.endswith('\n') and not line.endswith('\r\n'):
                lines_to_insert.append(line[:-1] + '\r\n')
            elif line.endswith('\r\n'):
                lines_to_insert.append(line)
            else:
                lines_to_insert.append(line + '\r\n')
        return lines_to_insert

    def _remove_self_references(self, lines_to_insert):
        updated_lines_to_insert = []
        take_line = True
        indent_level_for_class = 0
        for line in lines_to_insert:
            current_indent_level = len(line) - len(line.lstrip())
            if len(line.strip()) > 0 and current_indent_level <= indent_level_for_class:
                take_line = True
            if line.startswith('class PopulateAzureSynapseNotebook'):
                indent_level_for_class = current_indent_level
                take_line = False
            if take_line and 'PopulateAzureSynapseNotebook' not in line and 'populate_synapse_nb' not in line:
                updated_lines_to_insert.append(line)
        return updated_lines_to_insert

    def _remove_edge_blanks(self, lines_to_insert):
        start_index = 0
        end_index = len(lines_to_insert) - 1
        while start_index <= end_index and not lines_to_insert[start_index].strip():
            start_index += 1
        while end_index >= start_index and not lines_to_insert[end_index].strip():
            end_index -= 1
        return lines_to_insert[start_index:end_index + 1]


    def _add_log(self, lines_to_insert):
        log_message =  [
            f"# Cell source code was retreived from {self.source_path}\r\n",
            f"# Update was conducted at {datetime.now(timezone.utc)}\r\n",
            f"# Update script: https://github.com/pretoriusdre/populate-synapse-nb\r\n",
            "#\r\n"
        ]
        log_message.extend(lines_to_insert)
        return log_message


    def _read_destination(self):
        with open(self.destination_path, 'r') as file:
            notebook_json = json.load(file)
        return notebook_json


    def _insert_source_to_json(self, notebook_json, lines_to_insert):
        notebook_json = copy.deepcopy(notebook_json)
        cells = notebook_json['properties']['cells']
        for cell in cells:
            new_cell_source = []
            inserted_code = False
            take_line = True
            source_lines = cell.get('source')
            for source_line in source_lines:
                if source_line.startswith('#</CODE>'):
                    take_line = True
                if take_line:
                    new_cell_source.append(source_line)
                if source_line.startswith('#<CODE>'):
                    take_line = False
                    new_cell_source.extend(lines_to_insert)
                    inserted_code = True
            if inserted_code:
                cell['source'] = new_cell_source
                break
        return notebook_json

    def _save_destination(self, notebook_json):
        with open(self.destination_path, 'w') as file:
            json.dump(notebook_json, file, indent='\t')


if __name__ == '__main__':
    PopulateAzureSynapseNotebook(source_path=None, destination_path=None).run()
