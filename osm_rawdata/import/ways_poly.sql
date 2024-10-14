--
-- PostgreSQL database dump
--

-- Dumped from database version 14.7 (Ubuntu 14.7-0ubuntu0.22.10.1)
-- Dumped by pg_dump version 14.7 (Ubuntu 14.7-0ubuntu0.22.10.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: ways_poly; Type: TABLE; Schema: public; Owner: rob
--

CREATE TABLE public.ways_poly (
    osm_id bigint NOT NULL,
    uid integer,
    "user" text,
    version integer,
    changeset integer,
    "timestamp" timestamp without time zone,
    tags jsonb,
    refs text,
    geom public.geometry(Polygon,4326),
    grid integer
);


ALTER TABLE public.ways_poly OWNER TO rob;

--
-- Name: ways_poly_geom_idx; Type: INDEX; Schema: public; Owner: rob
--

CREATE INDEX ways_poly_geom_idx ON public.ways_poly USING gist (geom) WITH (fillfactor='100');

ALTER TABLE public.ways_poly CLUSTER ON ways_poly_geom_idx;


--
-- Name: ways_poly_tags_idx; Type: INDEX; Schema: public; Owner: rob
--

CREATE INDEX ways_poly_tags_idx ON public.ways_poly USING gin (tags);


--
-- Name: ways_poly_tags_idx1; Type: INDEX; Schema: public; Owner: rob
--

CREATE INDEX ways_poly_tags_idx1 ON public.ways_poly USING gin (tags);


--
-- Name: ways_poly_tags_idx10; Type: INDEX; Schema: public; Owner: rob
--

CREATE INDEX ways_poly_tags_idx10 ON public.ways_poly USING gin (tags);


--
-- Name: ways_poly_tags_idx2; Type: INDEX; Schema: public; Owner: rob
--

CREATE INDEX ways_poly_tags_idx2 ON public.ways_poly USING gin (tags);


--
-- Name: ways_poly_tags_idx3; Type: INDEX; Schema: public; Owner: rob
--

CREATE INDEX ways_poly_tags_idx3 ON public.ways_poly USING gin (tags);


--
-- Name: ways_poly_tags_idx4; Type: INDEX; Schema: public; Owner: rob
--

CREATE INDEX ways_poly_tags_idx4 ON public.ways_poly USING gin (tags);


--
-- Name: ways_poly_tags_idx5; Type: INDEX; Schema: public; Owner: rob
--

CREATE INDEX ways_poly_tags_idx5 ON public.ways_poly USING gin (tags);


--
-- Name: ways_poly_tags_idx6; Type: INDEX; Schema: public; Owner: rob
--

CREATE INDEX ways_poly_tags_idx6 ON public.ways_poly USING gin (tags);


--
-- Name: ways_poly_tags_idx7; Type: INDEX; Schema: public; Owner: rob
--

CREATE INDEX ways_poly_tags_idx7 ON public.ways_poly USING gin (tags);


--
-- Name: ways_poly_tags_idx8; Type: INDEX; Schema: public; Owner: rob
--

CREATE INDEX ways_poly_tags_idx8 ON public.ways_poly USING gin (tags);


--
-- Name: ways_poly_tags_idx9; Type: INDEX; Schema: public; Owner: rob
--

CREATE INDEX ways_poly_tags_idx9 ON public.ways_poly USING gin (tags);


--
-- PostgreSQL database dump complete
--

