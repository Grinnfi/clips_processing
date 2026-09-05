import os

def create_processed_folder(path, output_path=None):
    if output_path:
        if os.path.exists(output_path):
            base_name = os.path.basename(output_path.rstrip('/\\'))
            processed_path = os.path.join(output_path, f'{base_name}_processed')
        else:
            processed_path = output_path
    else:
        processed_path = os.path.join(os.path.dirname(path), f'{os.path.basename(path).split(".")[0]}_processed')

    if not os.path.exists(processed_path):
        print(f'Criando diretório {processed_path}')
        os.makedirs(processed_path, exist_ok=True)
    return processed_path