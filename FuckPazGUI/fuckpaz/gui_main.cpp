// gui_main.cpp — FuckPaz GUI (Modern Dark Theme — Extract & Inject Tabs)

#include <windows.h>
#include <windowsx.h> // Necessário para GET_X_LPARAM
#include <commctrl.h>
#include <uxtheme.h>
#include <dwmapi.h>
#include <shellapi.h>
#include <shlobj.h>   // Necessário para selecionar pastas (SHBrowseForFolder)
#include <thread>
#include <string>
#include <vector>
#include "fuckpaz_core.h"
#include "resource.h"

#pragma comment(lib, "comctl32.lib")
#pragma comment(lib, "uxtheme.lib")
#pragma comment(lib, "dwmapi.lib")
#pragma comment(lib, "gdi32.lib")
#pragma comment(lib, "user32.lib")
#pragma comment(lib, "comdlg32.lib")
#pragma comment(lib, "shell32.lib")
#pragma comment(lib, "ole32.lib")

#pragma comment(linker, "\"/manifestdependency:type='win32' \
name='Microsoft.Windows.Common-Controls' version='6.0.0.0' \
processorArchitecture='*' publicKeyToken='6595b64144ccf1df' language='*'\"")

// ---------------------------------------------------------------------------
// IDs dos controles
// ---------------------------------------------------------------------------
#define ID_TXT_PAZ        101
#define ID_BTN_BROWSE_PAZ 102
#define ID_TXT_MODS       103
#define ID_BTN_BROWSE_MODS 104
#define ID_CMB_GAMES      105
#define ID_PRG_BAR        106
#define ID_TXT_STATUS     107
#define ID_BTN_ACTION     108 // Botão principal (Extrair ou Injetar)

// ---------------------------------------------------------------------------
// Paleta — GitHub-inspired dark
// ---------------------------------------------------------------------------
#define CLR_BG          RGB(13,  17,  23)
#define CLR_SURFACE     RGB(22,  27,  34)
#define CLR_CONTROL     RGB(22,  27,  34)
#define CLR_BORDER      RGB(48,  54,  61)
#define CLR_BORDER_HOV  RGB(88,  96, 105)
#define CLR_ACCENT      RGB(88, 166, 255)    // Azul (Extrair)
#define CLR_ACCENT_HOV  RGB(121, 187, 255)
#define CLR_ACCENT_DIM  RGB(31,  71, 116)
#define CLR_INJECT      RGB(35, 134, 54)     // Verde (Injetar)
#define CLR_INJECT_HOV  RGB(46, 160, 67)
#define CLR_INJECT_DIM  RGB(20,  50,  30)
#define CLR_TEXT        RGB(230, 237, 243)
#define CLR_TEXT_DIM    RGB(139, 148, 158)

// ---------------------------------------------------------------------------
// Globals
// ---------------------------------------------------------------------------
HWND hwndMain;
HWND hEditPaz, hBtnBrowsePaz;
HWND hEditMods, hBtnBrowseMods;
HWND hComboGames, hProgressBar, hStatusText, hBtnAction;
HFONT hFontUI, hFontSmall, hFontBold, hFontMono;
HBRUSH hBrushBg, hBrushSurface, hBrushControl, hBrushBorder;
std::vector<GameInfoGUI> gamesList;

int currentMode = 0; // 0 = Extrair, 1 = Injetar
bool gBrowsePazHover = false;
bool gBrowseModsHover = false;
bool gActionHover = false;

RECT rcTabExtract = { 0, 40, 100, 75 };
RECT rcTabInject = { 100, 40, 200, 75 };

// ---------------------------------------------------------------------------
// Helpers de desenho
// ---------------------------------------------------------------------------
static void FillRoundRect(HDC hdc, const RECT& rc, int r, COLORREF fill) {
    HBRUSH br = CreateSolidBrush(fill);
    HPEN pen = CreatePen(PS_SOLID, 1, fill);
    HGDIOBJ ob = SelectObject(hdc, br);
    HGDIOBJ op = SelectObject(hdc, pen);
    RoundRect(hdc, rc.left, rc.top, rc.right, rc.bottom, r, r);
    SelectObject(hdc, ob);
    SelectObject(hdc, op);
    DeleteObject(br);
    DeleteObject(pen);
}

static void DrawBorder(HWND hwnd, HDC hdcParent, COLORREF color) {
    if (!IsWindowVisible(hwnd)) return;
    RECT rc;
    GetWindowRect(hwnd, &rc);
    MapWindowPoints(HWND_DESKTOP, GetParent(hwnd), (LPPOINT)&rc, 2);
    HPEN pen = CreatePen(PS_SOLID, 1, color);
    HGDIOBJ op = SelectObject(hdcParent, pen);
    HGDIOBJ ob = SelectObject(hdcParent, GetStockObject(NULL_BRUSH));
    Rectangle(hdcParent, rc.left, rc.top, rc.right, rc.bottom);
    SelectObject(hdcParent, op);
    SelectObject(hdcParent, ob);
    DeleteObject(pen);
}

static void DrawLabel(HDC hdc, HFONT font, const char* text, int x, int y, int w, int h, COLORREF color) {
    RECT rc = { x, y, x + w, y + h };
    SelectObject(hdc, font);
    SetTextColor(hdc, color);
    SetBkMode(hdc, TRANSPARENT);
    DrawTextA(hdc, text, -1, &rc, DT_LEFT | DT_VCENTER | DT_SINGLELINE);
}

// ---------------------------------------------------------------------------
// Lógica de Atualização da Interface (Troca de Abas)
// ---------------------------------------------------------------------------
void UpdateUIForMode() {
    // Escondemos o campo extra nos DOIS modos agora!
    ShowWindow(hEditMods, SW_HIDE);
    ShowWindow(hBtnBrowseMods, SW_HIDE);

    if (currentMode == 0) {
        SetWindowTextA(hBtnAction, "Extrair Arquivos do PAZ");
    }
    else {
        SetWindowTextA(hBtnAction, "Injetar Arquivos no PAZ");
    }
    InvalidateRect(hwndMain, NULL, TRUE);
}

// ---------------------------------------------------------------------------
// Subclasses
// ---------------------------------------------------------------------------
static LRESULT CALLBACK BtnSubclassProc(HWND hwnd, UINT uMsg, WPARAM wParam, LPARAM lParam, UINT_PTR uIdSubclass, DWORD_PTR dwRefData) {
    bool* pHover = reinterpret_cast<bool*>(dwRefData);

    switch (uMsg) {
    case WM_ERASEBKGND: return 1;
    case WM_PAINT: {
        PAINTSTRUCT ps;
        HDC hdc = BeginPaint(hwnd, &ps);
        RECT rc;
        GetClientRect(hwnd, &rc);
        bool disabled = !IsWindowEnabled(hwnd);
        COLORREF bg;

        if (uIdSubclass == ID_BTN_ACTION) {
            if (currentMode == 0) { // Azul para Extrair
                bg = disabled ? CLR_ACCENT_DIM : (*pHover ? CLR_ACCENT_HOV : CLR_ACCENT);
            }
            else { // Verde para Injetar
                bg = disabled ? CLR_INJECT_DIM : (*pHover ? CLR_INJECT_HOV : CLR_INJECT);
            }
        }
        else { // Botões Procurar
            bg = *pHover ? RGB(48, 54, 61) : CLR_SURFACE;
        }

        FillRoundRect(hdc, rc, 6, bg);

        char text[64];
        GetWindowTextA(hwnd, text, 64);
        SetBkMode(hdc, TRANSPARENT);
        SetTextColor(hdc, disabled ? CLR_TEXT_DIM : (uIdSubclass == ID_BTN_ACTION ? RGB(255, 255, 255) : CLR_TEXT));
        SelectObject(hdc, (uIdSubclass == ID_BTN_ACTION) ? hFontBold : hFontUI);
        DrawTextA(hdc, text, -1, &rc, DT_CENTER | DT_VCENTER | DT_SINGLELINE);

        if (uIdSubclass != ID_BTN_ACTION) { // Borda nos botões secundários
            HPEN pen = CreatePen(PS_SOLID, 1, *pHover ? CLR_BORDER_HOV : CLR_BORDER);
            HGDIOBJ op = SelectObject(hdc, pen);
            SelectObject(hdc, GetStockObject(NULL_BRUSH));
            RoundRect(hdc, rc.left, rc.top, rc.right - 1, rc.bottom - 1, 6, 6);
            SelectObject(hdc, op);
            DeleteObject(pen);
        }
        EndPaint(hwnd, &ps);
        return 0;
    }
    case WM_MOUSEMOVE:
        if (!*pHover) {
            *pHover = true;
            TRACKMOUSEEVENT tme = { sizeof(tme), TME_LEAVE, hwnd, 0 };
            TrackMouseEvent(&tme);
            InvalidateRect(hwnd, NULL, FALSE);
        }
        break;
    case WM_MOUSELEAVE:
        *pHover = false;
        InvalidateRect(hwnd, NULL, FALSE);
        break;
    case WM_SETCURSOR:
        SetCursor(LoadCursor(NULL, IDC_HAND));
        return TRUE;
    }
    return DefSubclassProc(hwnd, uMsg, wParam, lParam);
}

static LRESULT CALLBACK EditSubclassProc(HWND hwnd, UINT uMsg, WPARAM wParam, LPARAM lParam, UINT_PTR, DWORD_PTR) {
    if (uMsg == WM_NCPAINT) return 0;
    if (uMsg == WM_SETCURSOR) { SetCursor(LoadCursor(NULL, IDC_IBEAM)); return TRUE; }
    return DefSubclassProc(hwnd, uMsg, wParam, lParam);
}

// ---------------------------------------------------------------------------
// Threads Conectadas ao Core Real
// ---------------------------------------------------------------------------

// 1. Função que o Core chama para animar a nossa interface
void OnProgressUpdate(int current, int total, const std::string& filename) {
    if (hProgressBar) {
        SendMessage(hProgressBar, PBM_SETRANGE, 0, MAKELPARAM(0, total));
        SendMessage(hProgressBar, PBM_SETPOS, current, 0);
    }
    if (hStatusText) {
        std::string status = "Extraindo: " + filename;
        SetWindowTextA(hStatusText, status.c_str());
    }
}

// 2. A Thread Real de Extração
void ExtractionThread(std::string filePath, int gameIndex) {
    EnableWindow(hBtnAction, FALSE);
    SetWindowTextA(hStatusText, "Iniciando extração... Aguarde.");

    // CHAMADA REAL AO SEU CORE:
    // Passamos o arquivo PAZ, o índice do jogo, "" (pasta padrão) e a nossa função de progresso.
    int result = ProcessPaz(filePath, gameIndex, "", OnProgressUpdate);

    if (result == 0) {
        SetWindowTextA(hStatusText, "Extração concluída com sucesso!");
        MessageBoxA(hwndMain, "Arquivos extraídos com sucesso!", "FuckPaz GUI", MB_OK | MB_ICONINFORMATION);
    }
    else {
        SetWindowTextA(hStatusText, "Erro durante a extração.");
        MessageBoxA(hwndMain, "Ocorreu um erro ao tentar ler o arquivo PAZ.", "Erro", MB_OK | MB_ICONERROR);
    }

    SendMessage(hProgressBar, PBM_SETPOS, 0, 0);
    EnableWindow(hBtnAction, TRUE);
}

// 3. A Thread de Injeção
void InjectionThread(std::string pazPath, std::string outPazPath, int gameIndex) {
    EnableWindow(hBtnAction, FALSE);
    SetWindowTextA(hStatusText, "Iniciando reempacotamento... Isso pode demorar.");

    int result = ProcessPaz(pazPath, gameIndex, outPazPath, OnProgressUpdate);

    if (result == 0) {
        SetWindowTextA(hStatusText, "Injeção concluída com sucesso!");
        MessageBoxA(hwndMain, "Novo arquivo PAZ gerado com sucesso!", "Sucesso", MB_OK | MB_ICONINFORMATION);
    }
    else {
        SetWindowTextA(hStatusText, "Erro durante a injeção.");
        MessageBoxA(hwndMain, "Falha ao tentar injetar/reempacotar os arquivos.", "Erro", MB_OK | MB_ICONERROR);
    }

    SendMessage(hProgressBar, PBM_SETPOS, 0, 0); // Reseta a barra
    EnableWindow(hBtnAction, TRUE);
}

// ---------------------------------------------------------------------------
// Função principal da Janela
// ---------------------------------------------------------------------------
LRESULT CALLBACK WindowProc(HWND hwnd, UINT uMsg, WPARAM wParam, LPARAM lParam) {
    switch (uMsg) {
    case WM_CREATE: {
        hwndMain = hwnd;

        // Fontes
        hFontUI = CreateFontA(-13, 0, 0, 0, FW_NORMAL, 0, 0, 0, DEFAULT_CHARSET, 0, 0, CLEARTYPE_QUALITY, 0, "Segoe UI");
        hFontSmall = CreateFontA(-11, 0, 0, 0, FW_NORMAL, 0, 0, 0, DEFAULT_CHARSET, 0, 0, CLEARTYPE_QUALITY, 0, "Segoe UI");
        hFontBold = CreateFontA(-13, 0, 0, 0, FW_SEMIBOLD, 0, 0, 0, DEFAULT_CHARSET, 0, 0, CLEARTYPE_QUALITY, 0, "Segoe UI");
        hFontMono = CreateFontA(-12, 0, 0, 0, FW_NORMAL, 0, 0, 0, DEFAULT_CHARSET, 0, 0, CLEARTYPE_QUALITY, 0, "Consolas");

        hBrushBg = CreateSolidBrush(CLR_BG);
        hBrushSurface = CreateSolidBrush(CLR_SURFACE);
        hBrushControl = CreateSolidBrush(CLR_CONTROL);
        hBrushBorder = CreateSolidBrush(CLR_BORDER);

        // Seção: PAZ (Alvo ou Referência)
        hEditPaz = CreateWindowExA(0, "EDIT", "", WS_CHILD | WS_VISIBLE | ES_AUTOHSCROLL | ES_READONLY,
            20, 105, 334, 28, hwnd, (HMENU)ID_TXT_PAZ, NULL, NULL);
        SendMessage(hEditPaz, WM_SETFONT, (WPARAM)hFontMono, TRUE);
        SetWindowSubclass(hEditPaz, EditSubclassProc, 0, 0);

        hBtnBrowsePaz = CreateWindowA("BUTTON", "Procurar", WS_CHILD | WS_VISIBLE,
            360, 105, 90, 28, hwnd, (HMENU)ID_BTN_BROWSE_PAZ, NULL, NULL);
        SetWindowSubclass(hBtnBrowsePaz, BtnSubclassProc, ID_BTN_BROWSE_PAZ, (DWORD_PTR)&gBrowsePazHover);

        // Seção: MODS (Apenas Injeção)
        hEditMods = CreateWindowExA(0, "EDIT", "", WS_CHILD | ES_AUTOHSCROLL | ES_READONLY, // Inicialmente invisível
            20, 160, 334, 28, hwnd, (HMENU)ID_TXT_MODS, NULL, NULL);
        SendMessage(hEditMods, WM_SETFONT, (WPARAM)hFontMono, TRUE);
        SetWindowSubclass(hEditMods, EditSubclassProc, 0, 0);

        hBtnBrowseMods = CreateWindowA("BUTTON", "Procurar", WS_CHILD, // Inicialmente invisível
            360, 160, 90, 28, hwnd, (HMENU)ID_BTN_BROWSE_MODS, NULL, NULL);
        SetWindowSubclass(hBtnBrowseMods, BtnSubclassProc, ID_BTN_BROWSE_MODS, (DWORD_PTR)&gBrowseModsHover);

        // Seção: Jogos
        hComboGames = CreateWindowA("COMBOBOX", "", CBS_DROPDOWNLIST | CBS_HASSTRINGS | WS_CHILD | WS_VISIBLE | WS_VSCROLL | CBS_OWNERDRAWFIXED,
            20, 220, 430, 200, hwnd, (HMENU)ID_CMB_GAMES, NULL, NULL);
        SendMessage(hComboGames, WM_SETFONT, (WPARAM)hFontUI, TRUE);

        gamesList = GetSupportedGamesList();
        for (const auto& g : gamesList) SendMessageA(hComboGames, CB_ADDSTRING, 0, (LPARAM)g.name.c_str());
        SendMessage(hComboGames, CB_SETCURSEL, 0, 0);

        // Status & Progresso
        hProgressBar = CreateWindowExA(0, PROGRESS_CLASS, NULL, WS_CHILD | WS_VISIBLE | PBS_SMOOTH,
            20, 280, 430, 8, hwnd, (HMENU)ID_PRG_BAR, NULL, NULL);
        SetWindowTheme(hProgressBar, L"", L"");
        SendMessage(hProgressBar, PBM_SETBARCOLOR, 0, (LPARAM)CLR_ACCENT);
        SendMessage(hProgressBar, PBM_SETBKCOLOR, 0, (LPARAM)CLR_BORDER);

        hStatusText = CreateWindowA("STATIC", "Aguardando ação...", WS_CHILD | WS_VISIBLE | SS_LEFT,
            20, 298, 430, 18, hwnd, (HMENU)ID_TXT_STATUS, NULL, NULL);
        SendMessage(hStatusText, WM_SETFONT, (WPARAM)hFontSmall, TRUE);

        // Botão de Ação (Único, muda dinamicamente)
        hBtnAction = CreateWindowA("BUTTON", "Extrair Arquivos PAZ", WS_CHILD | WS_VISIBLE,
            20, 325, 430, 38, hwnd, (HMENU)ID_BTN_ACTION, NULL, NULL);
        SetWindowSubclass(hBtnAction, BtnSubclassProc, ID_BTN_ACTION, (DWORD_PTR)&gActionHover);

        DragAcceptFiles(hwnd, TRUE);
        UpdateUIForMode(); // Configura a tela inicial
        return 0;
    }

    case WM_DROPFILES: {
        HDROP hDrop = (HDROP)wParam;
        char szFile[MAX_PATH] = { 0 };
        if (DragQueryFileA(hDrop, 0, szFile, MAX_PATH)) {
            DWORD attr = GetFileAttributesA(szFile);
            // Se for diretório e estivermos no modo de injeção, joga na caixa de Mods
            if ((attr & FILE_ATTRIBUTE_DIRECTORY) && currentMode == 1) {
                SetWindowTextA(hEditMods, szFile);
            }
            else {
                SetWindowTextA(hEditPaz, szFile); // Senão, assume que é o arquivo PAZ
            }
        }
        DragFinish(hDrop);
        return 0;
    }

    case WM_LBUTTONDOWN: {
        POINT pt = { GET_X_LPARAM(lParam), GET_Y_LPARAM(lParam) };
        // Lógica de clique nas abas
        if (PtInRect(&rcTabExtract, pt) && currentMode != 0) {
            currentMode = 0;
            SendMessage(hProgressBar, PBM_SETBARCOLOR, 0, (LPARAM)CLR_ACCENT); // Progresso azul
            UpdateUIForMode();
        }
        else if (PtInRect(&rcTabInject, pt) && currentMode != 1) {
            currentMode = 1;
            SendMessage(hProgressBar, PBM_SETBARCOLOR, 0, (LPARAM)CLR_INJECT); // Progresso verde
            UpdateUIForMode();
        }
        break;
    }

    case WM_ERASEBKGND: return 1;

    case WM_PAINT: {
        PAINTSTRUCT ps;
        HDC hdc = BeginPaint(hwnd, &ps);
        RECT rc; GetClientRect(hwnd, &rc);

        FillRect(hdc, &rc, hBrushBg); // Fundo geral

        // 1. Header escuro
        RECT hdr = { 0, 0, rc.right, 40 };
        FillRect(hdc, &hdr, hBrushSurface);
        DrawLabel(hdc, hFontBold, "FuckPaz", 18, 11, 120, 20, CLR_TEXT);
        DrawLabel(hdc, hFontSmall, "PAZ Extractor & Injector - By SekaiVN", 88, 13, 200, 18, CLR_TEXT_DIM);

        // 2. Área das Abas (Fundo levemente mais claro que o BG)
        RECT tabsArea = { 0, 40, rc.right, 75 };
        HBRUSH brTabs = CreateSolidBrush(RGB(18, 22, 28));
        FillRect(hdc, &tabsArea, brTabs);
        DeleteObject(brTabs);

        // Linha divisória fina abaixo das abas
        HPEN sep = CreatePen(PS_SOLID, 1, CLR_BORDER);
        HGDIOBJ op = SelectObject(hdc, sep);
        MoveToEx(hdc, 0, 74, NULL); LineTo(hdc, rc.right, 74);
        SelectObject(hdc, op); DeleteObject(sep);

        // Desenhar os botões/textos das abas
        DrawLabel(hdc, hFontBold, "Extrair", rcTabExtract.left, rcTabExtract.top, rcTabExtract.right - rcTabExtract.left, 35, currentMode == 0 ? CLR_TEXT : CLR_TEXT_DIM);
        DrawLabel(hdc, hFontBold, "Injetar", rcTabInject.left, rcTabInject.top, rcTabInject.right - rcTabInject.left, 35, currentMode == 1 ? CLR_TEXT : CLR_TEXT_DIM);

        // Sublinhado da aba ativa
        RECT activeTab = (currentMode == 0) ? rcTabExtract : rcTabInject;
        HBRUSH indicator = CreateSolidBrush((currentMode == 0) ? CLR_ACCENT : CLR_INJECT);
        RECT indRc = { activeTab.left + 15, activeTab.bottom - 2, activeTab.right - 45, activeTab.bottom };
        FillRect(hdc, &indRc, indicator);
        DeleteObject(indicator);

        // 3. Labels Dinâmicos dependendo da aba
        if (currentMode == 0) {
            DrawLabel(hdc, hFontSmall, "ARQUIVO PAZ (Alvo da extração)", 20, 90, 200, 12, CLR_TEXT_DIM);
        }
        else {
            DrawLabel(hdc, hFontSmall, "ARQUIVO PAZ ORIGINAL (Referência para injeção)", 20, 90, 300, 12, CLR_TEXT_DIM);

            DrawLabel(hdc, hFontSmall, "* Coloque seus arquivos modificados na mesma pasta em que está seu .PAZ original.", 20, 145, 430, 12, CLR_INJECT);
            DrawLabel(hdc, hFontSmall, "* O repack será gerado automaticamente como '_new.paz' nesta mesma pasta.", 20, 160, 430, 12, CLR_INJECT);
        }

        DrawLabel(hdc, hFontSmall, "MOTOR / JOGO ALVO", 20, 205, 200, 12, CLR_TEXT_DIM);

        // Desenhar bordas nos Edits e Combo
        DrawBorder(hEditPaz, hdc, CLR_BORDER);
        DrawBorder(hEditMods, hdc, CLR_BORDER);
        DrawBorder(hComboGames, hdc, CLR_BORDER);

        EndPaint(hwnd, &ps);
        return 0;
    }

                 // ... (WM_DRAWITEM, WM_MEASUREITEM, WM_CTLCOLORSTATIC, WM_CTLCOLOREDIT permanecem idênticos ao código anterior)

    case WM_CTLCOLORSTATIC: {
        HDC hdc = (HDC)wParam;
        SetBkMode(hdc, TRANSPARENT);
        SetTextColor(hdc, CLR_TEXT_DIM);
        return (LRESULT)hBrushBg;
    }
    case WM_CTLCOLOREDIT: {
        HDC hdc = (HDC)wParam;
        SetBkColor(hdc, CLR_SURFACE);
        SetTextColor(hdc, CLR_TEXT);
        return (LRESULT)hBrushSurface;
    }

    case WM_DRAWITEM: {
        LPDRAWITEMSTRUCT pDIS = (LPDRAWITEMSTRUCT)lParam;
        if (pDIS->CtlID != ID_CMB_GAMES) break;
        COLORREF bg = (pDIS->itemState & ODS_SELECTED) ? CLR_BORDER : CLR_SURFACE;
        HBRUSH br = CreateSolidBrush(bg);
        FillRect(pDIS->hDC, &pDIS->rcItem, br);
        DeleteObject(br);
        char buf[256]; SendMessage(pDIS->hwndItem, CB_GETLBTEXT, pDIS->itemID, (LPARAM)buf);
        SetBkMode(pDIS->hDC, TRANSPARENT); SetTextColor(pDIS->hDC, CLR_TEXT); SelectObject(pDIS->hDC, hFontUI);
        RECT rcText = pDIS->rcItem; rcText.left += 10;
        DrawTextA(pDIS->hDC, buf, -1, &rcText, DT_LEFT | DT_VCENTER | DT_SINGLELINE);
        return TRUE;
    }
    case WM_MEASUREITEM: {
        LPMEASUREITEMSTRUCT pMIS = (LPMEASUREITEMSTRUCT)lParam;
        if (pMIS->CtlID == ID_CMB_GAMES) { pMIS->itemHeight = 28; return TRUE; }
        break;
    }

    case WM_COMMAND: {
        if (LOWORD(wParam) == ID_BTN_BROWSE_PAZ) {
            OPENFILENAMEA ofn = {}; char szFile[260] = {};
            ofn.lStructSize = sizeof(ofn); ofn.hwndOwner = hwnd; ofn.lpstrFile = szFile; ofn.nMaxFile = sizeof(szFile);
            ofn.lpstrFilter = "Arquivos PAZ\0*.paz\0Todos os Arquivos\0*.*\0"; ofn.nFilterIndex = 1;
            ofn.Flags = OFN_PATHMUSTEXIST | OFN_FILEMUSTEXIST;
            if (GetOpenFileNameA(&ofn)) SetWindowTextA(hEditPaz, szFile);
        }

        else if (LOWORD(wParam) == ID_BTN_BROWSE_MODS) {
            OPENFILENAMEA ofn = {}; char szFile[260] = {};
            ofn.lStructSize = sizeof(ofn); ofn.hwndOwner = hwnd; ofn.lpstrFile = szFile; ofn.nMaxFile = sizeof(szFile);
            ofn.lpstrFilter = "Arquivos PAZ\0*.paz\0Todos os Arquivos\0*.*\0"; ofn.nFilterIndex = 1;
            ofn.lpstrDefExt = "paz"; // Adiciona .paz automaticamente
            ofn.Flags = OFN_PATHMUSTEXIST | OFN_OVERWRITEPROMPT;

            if (GetSaveFileNameA(&ofn)) {
                SetWindowTextA(hEditMods, szFile);
            }
        }
        else if (LOWORD(wParam) == ID_BTN_ACTION) {
            char pazPath[MAX_PATH] = {};
            GetWindowTextA(hEditPaz, pazPath, MAX_PATH);
            int sel = (int)SendMessage(hComboGames, CB_GETCURSEL, 0, 0);

            if (strlen(pazPath) == 0) {
                MessageBoxA(hwnd, "Selecione um arquivo PAZ primeiro.", "Aviso", MB_OK | MB_ICONWARNING);
                break;
            }

            if (currentMode == 0) { // Extrair
                if (sel != CB_ERR) std::thread(ExtractionThread, std::string(pazPath), gamesList[sel].index).detach();
            }
            else { // Injetar
                std::string inPath = pazPath;
                std::string outPath = inPath;

                // Procura o ".paz" no final do caminho e insere o "_new" antes dele
                size_t dotPos = outPath.find_last_of('.');
                if (dotPos != std::string::npos) {
                    outPath.insert(dotPos, "_new");
                }
                else {
                    outPath += "_new.paz"; // Caso bizarro sem extensão
                }

                // Passa a string gerada automaticamente para a Thread!
                if (sel != CB_ERR) std::thread(InjectionThread, inPath, outPath, gamesList[sel].index).detach();
            }
        }
        return 0;
    }

    case WM_DESTROY:
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProc(hwnd, uMsg, wParam, lParam);
}

// ---------------------------------------------------------------------------
// Entry Point
// ---------------------------------------------------------------------------
int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE, LPSTR, int nCmdShow) {
    INITCOMMONCONTROLSEX icc = { sizeof(icc), ICC_PROGRESS_CLASS | ICC_STANDARD_CLASSES };
    InitCommonControlsEx(&icc);

    const char CLASS_NAME[] = "FuckPazGUIClass";
    WNDCLASSEXA wc = {};
    wc.cbSize = sizeof(wc); wc.lpfnWndProc = WindowProc; wc.hInstance = hInstance;
    wc.lpszClassName = CLASS_NAME; wc.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
    wc.hCursor = LoadCursor(NULL, IDC_ARROW); wc.style = CS_HREDRAW | CS_VREDRAW;

    wc.hIcon = LoadIconA(hInstance, MAKEINTRESOURCEA(IDI_ICON1));
    wc.hIconSm = LoadIconA(hInstance, MAKEINTRESOURCEA(IDI_ICON1));
    RegisterClassExA(&wc);

    // Ajustei a altura para 420 para acomodar as abas confortavelmente
    HWND hwnd = CreateWindowExA(0, CLASS_NAME, "FuckPaz GUI",
        WS_OVERLAPPEDWINDOW ^ WS_THICKFRAME ^ WS_MAXIMIZEBOX,
        CW_USEDEFAULT, CW_USEDEFAULT, 470, 420, NULL, NULL, hInstance, NULL);

    BOOL dark = TRUE;
    if (FAILED(DwmSetWindowAttribute(hwnd, 20, &dark, sizeof(dark)))) DwmSetWindowAttribute(hwnd, 19, &dark, sizeof(dark));

    ShowWindow(hwnd, nCmdShow); UpdateWindow(hwnd);
    MSG msg = {};
    while (GetMessage(&msg, NULL, 0, 0)) { TranslateMessage(&msg); DispatchMessage(&msg); }
    return 0;
}