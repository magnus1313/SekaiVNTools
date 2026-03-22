#pragma once
#include <string>
#include <vector>
#include <functional>

// Estrutura para preencher a caixa de sele??o (ComboBox) da GUI
struct GameInfoGUI {
    int index;
    std::string name;
};

// Retorna a lista de jogos suportados
std::vector<GameInfoGUI> GetSupportedGamesList();

// Callback para atualizar a barra de progresso na interface
// current: arquivo atual | total: total de arquivos | filename: nome do arquivo atual
using PazProgressCallback = std::function<void(int current, int total, const std::string& filename)>;

// Fun??o principal de processamento que substituir? o antigo "int main"
// Retorna 0 em caso de sucesso ou outro valor para erro
int ProcessPaz(const std::string& in_filename, unsigned long game_index, const std::string& out_filename, PazProgressCallback progress_cb);