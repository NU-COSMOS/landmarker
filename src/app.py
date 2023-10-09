import datetime
import pickle
import shutil
import tkinter as tk
from tkinter import Tk
from tkinter import ttk
from tkinter import messagebox
from typing import List, Literal
from pathlib import Path
from PIL import Image, ImageTk

from match import Match
from colors import get_colors

# チーム名等に含められない文字
NGCHARAS = ["_", ".", "/", "\\", '"', "'"]


class Application(tk.Frame):
    teams = Path('teams')  # チームデータ保存用ディレクトリ
    maps = Path('maps')  # マップ画像ディレクトリ
    tmp = Path('tmp')  # ランドマークデータ一時保存用ディレクトリ

    def __init__(self, root: Tk, w: int, h: int) -> None:
        super().__init__(root, width=w, height=h)
        # 必要なディレクトリ
        if not self.maps.is_dir():
            self.maps.mkdir(exist_ok=False)
            messagebox.showerror("エラー", "マップデータが見つかりません\nmapsディレクトリにmap画像を置いてください")
            exit(1)
        self.teams.mkdir(exist_ok=True)
        self.tmp.mkdir(exist_ok=True)

        # 設定関連
        self.r = 5  # 描画する点の半径
        self.font = ("", 15)
        self.default_map = 'Erangel.jpg'

        # クリックした座標を格納しておくリスト
        self.pts = []

        self.root = root
        self.pack()
        self.pack_propagate(0)
        self.create_main_widgets()


    def create_main_widgets(self, frame: tk.Frame=None) -> None:
        """
        アプリ起動時の画面
        
        Args:
            frame (tk.Frame): 消したいフレーム
        """
        if frame is not None:
            frame.destroy()

        self.main_frame = tk.Frame(self)
        
        # 記録ボタン
        recode_mode_btn = tk.Button(self.main_frame,
                                    text='記録',
                                    font=self.font,
                                    command=lambda: self.create_record_widgets(frame=self.main_frame))
        recode_mode_btn.pack(side='left')

        # 閲覧ボタン
        view_mode_btn = tk.Button(self.main_frame,
                                  text='閲覧',
                                  font=self.font,
                                  command=lambda: self.create_view_widgets(frame=self.main_frame))
        view_mode_btn.pack(side='left')

        # 編集ボタン
        edit_mode_btn = tk.Button(self.main_frame,
                                  text='終了',
                                  font=self.font,
                                  command=self.root.destroy)
        edit_mode_btn.pack(side='left')

        self.main_frame.pack()


    def create_view_widgets(self,
                            map_name: str=None,
                            frame: tk.Frame=None) -> None:
        """
        閲覧画面

        Args:
            map_name (str): 表示するマップ名
            frame (tk.Frame): 消したいフレーム
        """
        global map_img

        if frame is not None:
            frame.destroy()
        view = tk.Frame(self)

        # 画面左側
        left = tk.Frame(view)

        # マップ一覧
        map_list = tk.Listbox(left, exportselection=False, font=self.font)
        for m in self.maps.iterdir():
            if m.is_file():
                map_list.insert(0, m.name)
        map_list.pack()

        # 表示可能なスクリム一覧
        matches = self.get_match_names()
        match_list = tk.Listbox(left, selectmode="multiple", exportselection=False, font=self.font)
        if len(matches):
            for m in matches:
                match_list.insert(0, m)
        match_list.pack()

        # 表示可能なチーム一覧
        teams = self.get_team_names()
        team_list = tk.Listbox(left, selectmode="multiple", exportselection=False, font=self.font)
        if len(teams):
            for team in teams:
                team_list.insert(0, team)
        team_list.pack()

        left.pack(side='left')

        # 画面右側
        self.right = tk.Frame(view)

        # 画面右上
        self.right_top = tk.Frame(self.right)

        legend = tk.Label(self.right_top,
                          text="表示中のチーム一覧",
                          font=self.font)
        legend.pack()

        self.show_team_list = tk.Listbox(self.right_top, font=self.font)
        # スクロールバー
        self.team_list_xbar = tk.Scrollbar(self.right_top, orient=tk.HORIZONTAL, command=self.show_team_list.xview)
        self.show_team_list['xscrollcommand'] = self.team_list_xbar.set
        self.team_list_xbar.pack(fill='x', side='bottom')
        self.team_list_ybar = tk.Scrollbar(self.right_top, orient=tk.VERTICAL, command=self.show_team_list.yview)
        self.show_team_list['yscrollcommand'] = self.team_list_ybar.set
        self.team_list_ybar.pack(fill='y', side='right')

        self.show_team_list.pack()

        self.right_top.pack()

        # 画面右下
        self.right_bottom = tk.Frame(self.right)

        # 今日の日付
        tokyo_tz = datetime.timezone(datetime.timedelta(hours=9))
        now = datetime.datetime.now(tokyo_tz)
        # 開始日付
        start_date_lbl = tk.Label(self.right_bottom, text='開始年月日', font=self.font)
        start_date_lbl.pack()
        start_years = [str(i)+'年' for i in range(int(now.year)-10, int(now.year)+2)]
        start_y_com = ttk.Combobox(self.right_bottom, state='readonly', values=start_years, font=self.font)
        start_y_com.current(0)
        start_y_com.pack()
        start_months = [str(i)+'月' for i in range(1, 13)]
        start_m_com = ttk.Combobox(self.right_bottom, state='readonly', values=start_months, font=self.font)
        start_m_com.current(0)
        start_m_com.pack()
        start_days = [str(i)+'日' for i in range(1, 32)]
        start_d_com = ttk.Combobox(self.right_bottom, state='readonly', values=start_days, font=self.font)
        start_d_com.current(0)
        start_d_com.pack()

        # 終了日付
        end_date_lbl = tk.Label(self.right_bottom, text='終了年月日', font=self.font)
        end_date_lbl.pack()
        end_years = [str(i)+'年' for i in range(int(now.year)-10, int(now.year)+2)]
        end_y_com = ttk.Combobox(self.right_bottom, state='readonly', values=end_years, font=self.font)
        end_y_com.current(11)
        end_y_com.pack()
        end_months = [str(i)+'月' for i in range(1, 13)]
        end_m_com = ttk.Combobox(self.right_bottom, state='readonly', values=end_months, font=self.font)
        end_m_com.current(11)
        end_m_com.pack()
        end_days = [str(i)+'日' for i in range(1, 32)]
        end_d_com = ttk.Combobox(self.right_bottom, state='readonly', values=end_days, font=self.font)
        end_d_com.current(11)
        end_d_com.pack()

        round_lbl = tk.Label(self.right_bottom,
                             text="ラウンド数")
        round_lbl.pack()
        rounds = ['all']
        for i in range(1, 48):
            rounds.append("R"+str(i))
        r_com = ttk.Combobox(self.right_bottom, state='readonly', values=rounds, font=self.font)
        r_com.current(0)
        r_com.pack()

        num_match_lbl = tk.Label(self.right_bottom,
                                 text='表示する試合数:')
        num_match_lbl.pack()

        # 表示する試合数
        num_match = tk.Entry(self.right_bottom, font=self.font)
        num_match.pack()

        # 表示ボタン
        view_btn = tk.Button(self.right_bottom,
                             text='表示',
                             font=self.font, 
                             command=lambda: self.show_data(
                                self.get_select(map_list),
                                self.get_selects(match_list),
                                self.get_selects(team_list),
                                datetime.datetime.date(datetime.datetime.strptime(f'{start_y_com.get()[:-1]}{start_m_com.get()[:-1]}{start_d_com.get()[:-1]}', '%Y%m%d')),
                                datetime.datetime.date(datetime.datetime.strptime(f'{end_y_com.get()[:-1]}{end_m_com.get()[:-1]}{end_d_com.get()[:-1]}', '%Y%m%d')),
                                r_com.get(),
                                view,
                                mode='last',
                                num=num_match.get()))
        view_btn.pack()

        # 閲覧モード終了
        end_btn = tk.Button(self.right_bottom,
                            text='終了',
                            font=self.font,
                            command=lambda: self.create_main_widgets(view))
        end_btn.pack()

        self.right_bottom.pack()

        self.right.pack(side='right')

        # 画面中央
        self.center = tk.Frame(view)
        # マップの表示
        if map_name is None:
            if self.default_map in [m.name for m in self.maps.iterdir() if m.is_file()]:
                map_img = Image.open(self.maps / self.default_map)
            else:
                map_img = Image.open(list(self.maps.iterdir())[0])
        else:
            map_img = Image.open(self.maps / map_name)
        # 表示マップを最大化
        center_width = self.winfo_width()
        center_height = self.winfo_height()
        canvas = tk.Canvas(self.center, width=center_width, height=center_height)
        if center_width > center_height:
            map_img = map_img.resize((center_height, center_height))
        else:
            map_img = map_img.resize((center_width, center_width))
        map_img = ImageTk.PhotoImage(image=map_img)
        canvas.create_image(0,
                            0,
                            image=map_img,
                            tag='map',
                            anchor=tk.NW)
        canvas.pack(fill='both')
        self.center.pack(fill='both')

        view.pack()


    def get_selects(self, listbox: tk.Listbox) -> List[str]:
        """
        複数選択されたリストボックスの値一覧を返す

        Args:
            listbox (tk.Listbox): 読み取るリストボックス
        """
        indices = listbox.curselection()

        # １つも選択されていない
        if not len(indices):
            return None

        # 項目を取得
        names = []
        for idx in indices:
            name = listbox.get(idx)
            names.append(name)
        
        return names


    def show_data(self,
                  map_name: str,
                  matches: List[str], 
                  teams: List[str],
                  start: datetime.date,
                  end: datetime.date,
                  rcount: str,
                  view: tk.Frame=None,
                  mode: Literal['all', 'last']='all',
                  num: str=None) -> None:
        """
        ランドマーク表示

        Args:
            map_name (str): マップ名
            matches (List[str]): 試合名一覧
            teams (List[str]): チーム名一覧
            start (datetime.date): 開始日
            end (datetime.date): 終了日
            rcount (str): ラウンド数(R1, R2, ..., all)
            view (tk.Frame): 画像を載せるフレーム
            mode (Literal['all', 'last']): 表示モード
            num (str): 表示する試合数
        """
        global map_img

        try:
            if num is not None:
                num = int(num)
            else:
                num = None
        except:
            messagebox.showerror("エラー", "半角数字で入力してください")
            return

        # 表示一覧を空にする
        if self.show_team_list is not None:
            self.show_team_list.delete(0, tk.END)

        if self.center is not None:
            self.center.destroy()

        self.center = tk.Frame(view)

        if map_name is None:
            if self.default_map in [m.name for m in self.maps.iterdir() if m.is_file()]:
                map_name = self.default_map
                map_img = Image.open(self.maps / self.default_map)
            else:
                map_name = list(self.maps.iterdir())[0]
                map_img = Image.open(list(self.maps.iterdir())[0])
        else:
            map_img = Image.open(self.maps / map_name)
        # 表示マップを最大化
        center_width = self.winfo_width()
        center_height = self.winfo_height()
        canvas = tk.Canvas(self.center, width=center_width, height=center_height)
        if center_width > center_height:
            map_img = map_img.resize((center_height, center_height))
        else:
            map_img = map_img.resize((center_width, center_width))
        map_img = ImageTk.PhotoImage(image=map_img)
        canvas.create_image(0,
                            0,
                            image=map_img,
                            tag='map',
                            anchor=tk.NW)

        # 表示する試合一覧を用意
        if matches == None:
            matches = self.get_match_names()
        if teams == None:
            teams = [t.name for t in self.teams.iterdir()]
        view_matches = []
        show_teams = []
        for team in self.teams.iterdir():
            # 表示したいチームの場合
            if team.name in teams:
                team_color = get_colors()[teams.index(team.name)%len(get_colors())]
                for match in team.iterdir():
                    # 表示したいスクリムかつ日付かつマップかつラウンドの場合
                    if match.stem.split('_')[1] in matches and \
                        (start <= datetime.datetime.date(datetime.datetime.strptime(match.stem.split('_')[3], '%Y-%m-%d')) <= end) and \
                        Path(map_name).stem == match.stem.split('_')[2] and \
                        (rcount == "all" or rcount == match.stem.split('_')[4]):
                        view_matches.append({'name': match, 'c': team_color})
                        if team.name not in show_teams:
                            show_teams.append(team.name)

        # 最新のみ表示の場合
        if mode == 'last':
            view_matches = self.get_last_match(view_matches, teams, num)

        # 1試合ごとにプロット
        for view_match in view_matches:
            with open(view_match['name'], 'rb') as f:
                m: Match = pickle.load(f)
                for pt in m.pts:
                    canvas.create_oval(pt["x"]*map_img.width()//pt["w"]-self.r, 
                                       pt['y']*map_img.height()//pt["h"]-self.r,
                                       pt["x"]*map_img.width()//pt["w"]+self.r,
                                       pt['y']*map_img.height()//pt["h"]+self.r,
                                       fill=view_match['c'])
        canvas.pack(fill='both')
        self.center.pack(fill='both')

        # 表示チーム一覧を作成
        for i, team_name in enumerate(show_teams):
            self.show_team_list.insert(i, team_name)
            self.show_team_list.itemconfig(i, {'fg': get_colors()[teams.index(team_name)%len(get_colors())]})

        view.pack()


    def get_last_match(self, matches: List[dict[Path, str]], teams: List[str], num: int=None) -> List[dict[Path, str]]:
        """
        表示する試合リストの各チームの最新マッチのみを返す

        Args:
            matches (List[dict[Path, str]]): 表示対象の試合一覧
            teams (List[str]): 表示対象のチーム一覧
            num (int): 表示する試合数

        Returns:
            List[dict[Path, str]]: 表示対象の試合の最新一覧
        """
        view_matches = []
        # 各チームごとに処理
        for team in teams:
            _matches = []
            # 全試合を見て、チーム名が一致したら一時保存リストに加える
            for match in matches:
                if match['name'].name.split('/')[-1].split('_')[0] == team:
                    _matches.append(match)

            # 日付でソート
            if len(_matches) > 0:
                _matches.sort(key=lambda x: (x['name'].name.split('/')[-1].split('_')[3], x['name'].name.split('/')[-1].split('_')[4]))
                
                # 表示する試合数が記録済みの試合数を超えていた場合や入力されていない場合は調整
                tmp = num
                if num > len(_matches) or num is None:
                    num = len(_matches)
                
                for n in range(num):
                    view_matches.append(_matches[-(n+1)])
                num = tmp

        return view_matches


    def get_team_names(self) -> List[str]:
        """
        現在記録されているチーム名一覧

        Returns:
            List[str]: チーム名一覧
        """
        teams = []
        for team in self.teams.iterdir():
            if team.is_dir():
                teams.append(team.name)
        return teams


    def get_match_names(self) -> List[str]:
        """
        現在記録されている試合名一覧

        Returns:
            List[str]: 試合名一覧
        """
        matches = []
        for team in self.teams.iterdir():
            if team.is_dir():
                for m in (self.teams / team.name).iterdir():
                    if m.is_file():
                        match_name = m.name.split('_')[1]
                        if match_name not in matches:
                            matches.append(match_name)
        return matches


    def create_record_widgets(self,
                              team_name: str=None,
                              frame: tk.Frame=None,
                              map_name: str=None,
                              rcount: int=1,
                              match_name: str=None,
                              year: str=None,
                              month: str=None,
                              day: str=None) -> None:
        """
        記録画面

        Args:
            team_name (str): チーム名
            frame (tk.Frame): 消したいフレーム
            map_name (str): マップ名
            rcount (int): ラウンド数
            match_name (str): 試合名
        """
        global map_img

        if frame is not None:
            frame.destroy()
        self.pts = []

        record = tk.Frame(self)
        
        # 画面左側
        left = tk.Frame(record)

        # チーム名
        team_lbl = tk.Label(left,
                            font=self.font,
                            text=f'チーム名')
        team_lbl.pack(side='top')
        team_entry = tk.Entry(left, font=self.font)
        if team_name is not None:
            team_entry.insert(0, team_name)
        team_entry.pack()

        # 大会名の入力
        match_input_lbl = tk.Label(left,
                                   font=self.font,
                                   text='スクリムorリーグ名を入力してください')
        match_input_lbl.pack()
        match_entry = tk.Entry(left, font=self.font)
        if match_name is not None:
            match_entry.insert(0, match_name)
        match_entry.pack()

        # マップ一覧
        map_list = tk.Listbox(left, font=self.font)
        for m in self.maps.iterdir():
            if m.is_file():
                map_list.insert(0, m.name)
        map_list.pack()

        # 表示マップの変更
        change_map_btn = tk.Button(left,
                                   text='マップ変更',
                                   font=self.font,
                                   command=lambda: self.change_map(map_list,
                                                                   team_entry.get(),
                                                                   match_entry.get(),
                                                                   int(r_com.get()[1:]),
                                                                   record,
                                                                   y_com.get(),
                                                                   m_com.get(),
                                                                   d_com.get()))
        change_map_btn.pack()

        # 日付の選択
        date_lbl = tk.Label(left,
                            text='年月日',
                            font=self.font)
        date_lbl.pack()
        tokyo_tz = datetime.timezone(datetime.timedelta(hours=9))
        now = datetime.datetime.now(tokyo_tz)
        years = [str(i)+'年' for i in range(int(now.year)-10, int(now.year)+2)]
        y_com = ttk.Combobox(left, state='readonly', values=years, font=self.font)
        if year is not None:
            y_com.current(years.index(year))
        y_com.pack()
        months = [str(i)+'月' for i in range(1, 13)]
        m_com = ttk.Combobox(left, state='readonly', values=months, font=self.font)
        if month is not None:
            m_com.current(months.index(month))
        m_com.pack()
        days = [str(i)+'日' for i in range(1, 32)]
        d_com = ttk.Combobox(left, state='readonly', values=days, font=self.font)
        if day is not None:
            d_com.current(days.index(day))
        d_com.pack()

        # ラウンド数
        round_lbl = tk.Label(left,
                             text="ラウンド数",
                             font=self.font)
        round_lbl.pack()
        rounds = ['R'+str(i) for i in range(1, 48)]
        r_com = ttk.Combobox(left, state='readonly', values=rounds, font=self.font)
        r_com.current(rounds.index("R"+str(rcount)))
        r_com.pack()


        left.pack(side='left')

        # 画面右側
        right = tk.Frame(record)
        
        # 画面右上
        right_top = tk.Frame(right)

        # 仮記録データ一覧
        match_list_lbl = tk.Label(right_top,
                                  text='仮記録一覧',
                                  font=self.font)
        match_list_lbl.pack()
        match_list = tk.Listbox(right_top, font=self.font)
        for m in self.tmp.iterdir():
            if m.is_file():
                match_list.insert(0, m.name)
        ybar = tk.Scrollbar(right_top, orient=tk.VERTICAL, command=match_list.yview)
        match_list['yscrollcommand'] = ybar.set
        ybar.pack(fill='y', side='right')
        xbar = tk.Scrollbar(right_top, orient=tk.HORIZONTAL, command=match_list.xview)
        match_list['xscrollcommand'] = xbar.set
        xbar.pack(fill='x', side='bottom')
        match_list.pack(fill='both')

        right_top.pack()

        # 画面右下
        right_bottom = tk.Frame(right)

        # 仮記録データ削除ボタン
        del_btn = tk.Button(right_bottom,
                            text='仮記録削除',
                            font=self.font,
                            command=lambda: self.delete_tmp_match(team_entry.get(),
                                                                  match_list,
                                                                  map_name,
                                                                  match_entry.get(),
                                                                  int(r_com.get()[1:]),
                                                                  record,
                                                                  y_com.get(),
                                                                  m_com.get(),
                                                                  d_com.get()))
        del_btn.pack()

        # 仮記録データ保存ボタン
        tmp_save_btn = tk.Button(right_bottom,
                                 text='仮記録',
                                 font=self.font,
                                 command=lambda: self.tmp_save(team_entry.get(),
                                                               match_entry.get(),
                                                               map_name,
                                                               y_com.get(),
                                                               m_com.get(),
                                                               d_com.get(),
                                                               r_com.get()[1:],
                                                               map_img_w,
                                                               map_img_h,
                                                               record))
        tmp_save_btn.pack()

        # 仮記録データを確定保存
        save_btn = tk.Button(right_bottom,
                             text='記録',
                             font=self.font,
                             command=lambda: self.save(list(self.tmp.iterdir()),
                                                       record,
                                                       map_name,
                                                       int(r_com.get()[1:]),
                                                       match_entry.get(),
                                                       y_com.get(),
                                                       m_com.get(),
                                                       d_com.get()))
        save_btn.pack()

        # 記録モード終了
        end_btn = tk.Button(right_bottom,
                            text='終了',
                            font=self.font,
                            command=lambda: self.create_main_widgets(record))
        end_btn.pack()

        right_bottom.pack()

        right.pack(side='right')

        # 画面中央(マップ表示部分)
        center = tk.Frame(record)

        # マップの表示
        if map_name is None:
            if self.default_map in [m.name for m in self.maps.iterdir() if m.is_file()]:
                map_img = Image.open(self.maps / self.default_map)
            else:
                map_img = Image.open(list(self.maps.iterdir())[0])
        else:
            map_img = Image.open(self.maps / map_name)
        # 表示マップを最大化
        center_width = self.winfo_width()
        center_height = self.winfo_height()
        canvas = tk.Canvas(center, width=center_width, height=center_height)
        if center_width > center_height:
            map_img = map_img.resize((center_height, center_height))
        else:
            map_img = map_img.resize((center_width, center_width))
        map_img = ImageTk.PhotoImage(image=map_img)
        map_img_w = map_img.width()
        map_img_h = map_img.height()
        canvas.create_image(0,
                            0,
                            image=map_img,
                            tag='map',
                            anchor=tk.NW)
        canvas.pack(fill='both')
        canvas.bind('<ButtonPress-1>', self.plot)
        canvas.bind('<ButtonPress-1>', self.set_pt, '+')
        center.pack(fill='both')

        record.pack()


    def save(self,
             matches: List[Path],
             frame: tk.Frame=None,
             map_name: str=None,
             rcount: int=1,
             match_name: str=None,
             year: str=None,
             month: str=None,
             day: str=None) -> None:
        """
        記録

        Args:
            matches (List[Path]): 記録対象の仮記録データ一覧
            frame (tk.Frame): 消したいフレーム
            map_name (str): マップ名
            rcount (int): ラウンド数
            match_name (str): 試合名
            year (str): 年
            month (str): 月
            day (str): 日
        """
        if not len(matches):
            messagebox.showerror("エラー", '仮記録されたデータがありません')
            return

        for match in matches:
            team_name = str(match.name).split('_')[0]
            if (self.teams / team_name / match.name).exists():
                ret = messagebox.askyesno("そのデータ名は既に存在します。上書きしてよろしいですか？")
                if not ret:
                    return
            shutil.move(match, self.teams / team_name)

        self.create_record_widgets(team_name, frame, map_name, rcount, match_name, year, month, day)



    def tmp_save(self,
                 team_name: str,
                 match_name: str,
                 map_name: str,
                 year: str,
                 month: str,
                 day: str,
                 rcount: str,
                 img_w: int,
                 img_h: int,
                 frame: tk.Frame=None) -> None:
        """
        仮記録

        Args:
            team_name (str): チーム名
            match_name (str): スクリム(リーグ)名
            map_name (str): マップ名
            year (str): 年
            month (str): 月
            day (str): 日
            rcount (str): ラウンド数
            img_w (int): マップ画像幅
            img_h (int): マップ画像高さ
            frame (tk.Frame): 消したいフレーム
        """
        # チーム名が入力されているか
        if team_name is None:
            messagebox.showerror("エラー", 'チーム名が未入力です')
            return

        # スクリム名が入力されているか
        if match_name is None:
            messagebox.showerror("エラー", 'スクリム名が未入力です')
            return

        # 使用可能な文字かチェック
        for char in NGCHARAS:
            if char in team_name:
                messagebox.showerror("エラー", f'"{char}"をチーム名に含めないでください')
                return
            if char in match_name:
                messagebox.showerror("エラー", f'"{char}"をスクリム名に含めないでください')
                return

        # チームディレクトリが存在するかチェック
        team_dir = (self.teams / team_name)
        if not (team_dir.exists() and team_dir.is_dir()):
            ret = messagebox.askyesno('確認', 'そのチーム名は未登録です\n新しいチームとして登録しますか？')
            if ret:
                team_dir.mkdir(exist_ok=False)
            else:
                return

        # 試合名をチェック
        if match_name is None:
            messagebox.showerror("エラー", "スクリム(リーグ)名を入力してください")
            return

        if map_name is None:
            map_name = self.default_map

        # 日付チェック
        date = year[:-1] + month[:-1] + day[:-1]
        try:
            date = datetime.datetime.strptime(date, '%Y%m%d')
            date = datetime.datetime.date(date)
        except ValueError:
            messagebox.showerror("エラー", "日付の形式が無効です")
            return

        # 記録対象の座標があるかチェック
        if not len(self.pts):
            messagebox.showerror("エラー", "記録する座標がありません")
            return

        if len(self.pts) > 4:
            messagebox.showerror("エラー", "点の数が多すぎます\n一試合一チームずつ仮記録してください")
            self.create_record_widgets(team_name, frame, map_name, int(rcount), match_name, year, month, day)
            return

        pts = []
        for pt in self.pts:
            p = {}
            p['x'] = pt[0]
            p['y'] = pt[1]
            p['w'] = img_w
            p['h'] = img_h
            pts.append(p)
        self.pts = []

        # Matchオブジェクトを作成
        data = Match(team_name, match_name, map_name, date, int(rcount), pts)

        # 仮記録
        filename = f'{team_name}_{match_name}_{Path(map_name).stem}_{str(date)}_R{rcount}.pkl'
        if (self.tmp / filename).exists():
            ret = messagebox.askyesno("重複", "その試合のデータは仮記録内に存在します。上書きしてよろしいですか？")
            if not ret:
                self.create_record_widgets(team_name, frame, map_name, int(rcount), match_name, year, month, day)
                return
        tmp_file = self.tmp / filename

        with open(tmp_file, 'wb') as f:
            pickle.dump(data, f)
        self.create_record_widgets(team_name, frame, map_name, int(rcount), match_name, year, month, day)


    def plot(self, event: tk.Event) -> None:
        """
        画像をクリックした位置に点を表示

        Args:
            event (tk.Event): マウスイベント(ワンクリック)
        """
        canvas: tk.Canvas = event.widget
        canvas.create_oval(event.x-self.r, event.y-self.r, event.x+self.r, event.y+self.r, fill='Red')


    def set_pt(self, event: tk.Event) -> None:
        """
        クリックされた座標を格納
        
        Args:
            event (tk.Event): マウスイベント(ワンクリック)
        """
        self.pts.append([event.x, event.y])


    def get_select(self, listbox: tk.Listbox) -> str:
        """
        選択されたマップ名を返す

        Args:
            listbox (tk.Listbox): 選択した値を一つだけ読み取りたいリストボックス
        """
        indices = listbox.curselection()

        # ２つ以上選択されているor１つも選択されていない
        if len(indices) != 1:
            return None

        # 項目を取得
        index = indices[0]
        name = listbox.get(index)

        return name


    def change_map(self,
                   listbox: tk.Listbox,
                   team_name: str,
                   match_name: str,
                   rcount: int,
                   frame: tk.Frame=None,
                   year: str=None,
                   month: str=None,
                   day: str=None) -> None:
        """
        データ記録用表示マップを変更

        Args:
            listbox (tk.Listbox): マップ一覧のリストボックス
            team_name (str): チーム名
            match_name (str): 試合名
            rcount (int): ラウンド数
            frame (tk.Frame): 消したいフレーム
            year (str): 年
            month (str): 月
            day (str): 日
        """
        map_name = self.get_select(listbox)

        self.create_record_widgets(team_name, frame, map_name, rcount, match_name, year, month, day)


    def delete_tmp_match(self,
                         team_name: str,
                         listbox: tk.Listbox,
                         map_name: str,
                         match_name: str,
                         rcount: int,
                         frame: tk.Frame=None,
                         year: str=None,
                         month: str=None,
                         day: str=None) -> None:
        """
        選択した仮記録データを削除

        Args:
            team_name (str): チーム名
            listbox (tk.Listbox): 仮記録一覧
            map_name (str): マップ名
            match_name (str): 試合名
            rcount (int): ラウンド数
            frame (tk.Frame): 消したいフレーム
            year (str): 年
            month (str): 月
            day (str): 日
        """
        indices = listbox.curselection()

        # ２つ以上選択されているor１つも選択されていない
        if len(indices) != 1:
            messagebox.showerror("エラー", "一つずつ選択して消しましょう")
            self.create_record_widgets(team_name, frame, map_name, rcount, match_name, year, month, day) 

        # 項目を取得
        index = indices[0]
        del_match = listbox.get(index)

        # 削除
        del_path: Path = self.tmp / del_match
        del_path.unlink(missing_ok=False)

        self.create_record_widgets(team_name, frame, map_name, rcount, match_name, year, month, day)


def main():
    root = Tk()
    root.title('ランドマーク管理ツール')
    root.state('zoomed')
    app = Application(root, root.winfo_screenwidth(), root.winfo_screenheight())
    app.mainloop()


if __name__ == '__main__':
    main()